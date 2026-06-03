#!/usr/bin/env python3
"""Normalize ad-platform CSV exports to a single schema.

Reads a CSV exported from Google Ads, Meta Ads Manager, TikTok Ads,
LinkedIn Campaign Manager, or GA4, detects the platform from its
header columns (or accepts an explicit --platform override), and
emits a normalized CSV with these columns:

    platform, date, campaign, ad_set, ad, spend, impressions,
    clicks, conversions, conversion_value

Numeric fields are emitted as decimal strings. `spend` and
`conversion_value` are floats (2 dp). `impressions` and `clicks`
are integers. `conversions` is a float (Google Ads exports
fractional attribution like 0.73, so we preserve decimals). An
empty string means NULL.

Pure standard library. No pip install needed.

Usage:
    python3 parse_csv.py input.csv
    python3 parse_csv.py input.csv --platform meta --out normalized.csv
    cat export.csv | python3 parse_csv.py - --platform google
    python3 parse_csv.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import IO, Iterable

NORMALIZED_FIELDS = [
    "platform",
    "date",
    "campaign",
    "ad_set",
    "ad",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "conversion_value",
]

PLATFORMS = ("google", "meta", "tiktok", "linkedin", "ga4")

DECIMAL_SEP_CHOICES = ("auto", "period", "comma")


@dataclass
class PlatformProfile:
    """Map a platform's export columns to our normalized fields.

    Values are lists of candidate header names (case-insensitive,
    whitespace-stripped). The first match wins. A None field means
    the platform does not expose that data.
    """

    name: str
    fingerprint: tuple[str, ...]  # headers that strongly suggest this platform
    date: tuple[str, ...]
    campaign: tuple[str, ...]
    ad_set: tuple[str, ...] | None
    ad: tuple[str, ...] | None
    spend: tuple[str, ...]
    impressions: tuple[str, ...]
    clicks: tuple[str, ...]
    conversions: tuple[str, ...] | None
    conversion_value: tuple[str, ...] | None
    date_format: tuple[str, ...] = ()  # canonical date formats for this platform


# Highly-specific fingerprint tokens — tokens that essentially only
# appear in one platform's export and are enough on their own to
# identify the platform. Used by detect_platform() to allow a
# single-token match when the token is unambiguous.
HIGHLY_SPECIFIC_FINGERPRINTS: dict[str, frozenset[str]] = {
    "google": frozenset({"impr."}),
    "meta": frozenset({"amount spent (usd)"}),
    "tiktok": frozenset({"stat time day"}),
    "linkedin": frozenset({"campaign group name", "start date (in utc)"}),
    "ga4": frozenset({"session source / medium", "session campaign"}),
}


PROFILES: dict[str, PlatformProfile] = {
    "google": PlatformProfile(
        name="google",
        fingerprint=("campaign", "impr.", "cost"),
        date=("day", "date"),
        campaign=("campaign",),
        ad_set=("ad group",),
        ad=("ad", "headline 1"),
        spend=("cost",),
        impressions=("impr.", "impressions"),
        clicks=("clicks",),
        conversions=("conversions",),
        conversion_value=("conv. value", "all conv. value"),
        date_format=("%Y-%m-%d",),
    ),
    "meta": PlatformProfile(
        name="meta",
        fingerprint=("campaign name", "amount spent (usd)", "reach"),
        date=("reporting starts", "day", "date"),
        campaign=("campaign name",),
        ad_set=("ad set name",),
        ad=("ad name",),
        spend=("amount spent (usd)", "amount spent", "spend"),
        impressions=("impressions",),
        clicks=("clicks (all)", "link clicks", "clicks"),
        conversions=("results", "website purchases", "purchases", "leads"),
        conversion_value=(
            "purchases conversion value",
            "website purchases conversion value",
            "conversion value",
        ),
        date_format=("%Y-%m-%d",),
    ),
    "tiktok": PlatformProfile(
        name="tiktok",
        fingerprint=("campaign name", "cost", "cpm"),
        date=("by day", "stat time day", "date"),
        campaign=("campaign name",),
        ad_set=("ad group name",),
        ad=("ad name",),
        spend=("cost",),
        impressions=("impressions",),
        clicks=("clicks (destination)", "clicks"),
        conversions=("conversions", "total conversions"),
        conversion_value=("total complete payment value", "conversion value"),
        date_format=("%Y-%m-%d",),
    ),
    "linkedin": PlatformProfile(
        name="linkedin",
        fingerprint=("campaign name", "total spent", "campaign group name"),
        date=("start date (in utc)", "start date", "date"),
        campaign=("campaign name",),
        ad_set=("campaign group name",),
        ad=("ad name", "creative name"),
        spend=("total spent", "amount spent"),
        impressions=("impressions",),
        clicks=("clicks",),
        conversions=("conversions", "external website conversions"),
        conversion_value=("conversion value",),
        date_format=("%Y-%m-%d", "%m/%d/%Y"),
    ),
    "ga4": PlatformProfile(
        name="ga4",
        fingerprint=("session source / medium", "sessions"),
        date=("date", "first session date"),
        campaign=("session campaign", "campaign"),
        ad_set=None,
        ad=None,
        spend=("advertising cost", "cost"),
        impressions=("impressions",),
        clicks=("clicks",),
        conversions=("conversions", "key events", "purchases"),
        conversion_value=("total revenue", "purchase revenue"),
        date_format=("%Y%m%d", "%Y-%m-%d"),
    ),
}


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", h.strip().lower())


def detect_platform(headers: list[str]) -> str | None:
    """Pick the platform whose fingerprint or specific token best matches.

    A platform claims a match in either of two ways:

    1. Highly-specific token — any token in HIGHLY_SPECIFIC_FINGERPRINTS
       for that platform appears in the headers. This is sufficient on
       its own (we trust these tokens because they essentially only
       appear in that platform's export).
    2. Fingerprint score — at least 2 of the platform's fingerprint
       headers appear in the headers.

    Highly-specific matches win over score-only matches. Ties within
    each tier are broken by raw fingerprint score, then by registration
    order in PROFILES.
    """
    norm = {_norm_header(h) for h in headers}
    specific_match: tuple[int, str | None] = (-1, None)
    score_match: tuple[int, str | None] = (0, None)
    for name, profile in PROFILES.items():
        score = sum(1 for fp in profile.fingerprint if fp in norm)
        specific = HIGHLY_SPECIFIC_FINGERPRINTS.get(name, frozenset())
        has_specific = bool(specific & norm)
        if has_specific and score > specific_match[0]:
            specific_match = (score, name)
        if score >= 2 and score > score_match[0]:
            score_match = (score, name)
    # Highly-specific match wins regardless of score (it can claim with score 0).
    if specific_match[1] is not None:
        return specific_match[1]
    return score_match[1]


def _find_column(headers: list[str], candidates: Iterable[str] | None) -> str | None:
    if not candidates:
        return None
    norm_map = {_norm_header(h): h for h in headers}
    for cand in candidates:
        if cand in norm_map:
            return norm_map[cand]
    return None


def _detect_decimal_separator(s: str) -> str:
    """Heuristically determine which character is the decimal separator.

    Returns '.', ',', or '' (no decimal — pure integer/thousands).
    Pre-condition: s contains only digits, '.', ',', and an optional
    leading '-'. Empty strings return ''.
    """
    has_dot = "." in s
    has_comma = "," in s
    if not has_dot and not has_comma:
        return ""
    if has_dot and has_comma:
        # Whichever appears last is the decimal separator.
        return "." if s.rfind(".") > s.rfind(",") else ","
    if has_comma:  # only commas
        commas = s.count(",")
        if commas > 1:
            return ""  # all thousands separators
        # Exactly one comma. Disambiguate decimal vs thousands by the
        # digit-count of the group that follows:
        #   * 1 or 2 digits  -> decimal  (EU bare: "0,5" / "123,45")
        #   * exactly 3      -> thousands (US convention: "1,234")
        #   * 4 or more      -> decimal  (thousands groups are always
        #                                 exactly 3 digits; anything
        #                                 longer can't be a thousands
        #                                 group, so prefer decimal:
        #                                 "1,2345" -> 1.2345)
        after = s.split(",")[1]
        if not after.isdigit():
            return ""
        if len(after) == 3:
            return ""
        return ","
    # only dots
    dots = s.count(".")
    if dots > 1:
        return ""  # all thousands separators (EU style: 1.234.567)
    after = s.split(".")[1]
    # Default to US: a single period is the decimal separator unless
    # it looks like EU thousands (exactly 3 digits after, no digits
    # before — but even then we default to US per the spec).
    if after.isdigit():
        return "."
    return ""


def _normalize_numeric_string(s: str, decimal_sep: str = "auto") -> str:
    """Strip thousands separators and return a parseable decimal string.

    `decimal_sep` is one of:
      * 'auto'   — heuristically detect (see _detect_decimal_separator)
      * 'period' — '.' is decimal, ',' is thousands
      * 'comma'  — ',' is decimal, '.' is thousands

    Input must already be limited to digits, '.', ',', and an optional
    leading '-'. Returns a string parseable by float() (no thousands
    separators, decimal as '.').
    """
    if not s:
        return s
    sign = ""
    if s.startswith("-"):
        sign = "-"
        s = s[1:]
    if decimal_sep == "auto":
        sep = _detect_decimal_separator(s)
    elif decimal_sep == "period":
        sep = "." if "." in s else ""
    else:  # comma
        sep = "," if "," in s else ""
    if sep == "":
        # Both '.' and ',' are thousands separators (if present).
        cleaned = s.replace(",", "").replace(".", "")
    elif sep == ".":
        # '.' is decimal, ',' is thousands.
        cleaned = s.replace(",", "")
    else:  # sep == ","
        # ',' is decimal, '.' is thousands.
        cleaned = s.replace(".", "").replace(",", ".")
    return sign + cleaned


def _parse_currency(value: str, decimal_sep: str = "auto") -> str:
    """Strip currency symbols and thousands separators, return a decimal string.

    Handles accounting-style parentheses for negatives, e.g.
    ``(123.45)`` becomes ``-123.45``. Supports US (``1,234.56``) and
    European (``1.234,56``) number formats — see the
    ``decimal_sep`` argument and the ``--decimal-sep`` CLI flag.
    Returns '' for empty/missing values (treated as NULL downstream).
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in ("--", "n/a", "nan", "null"):
        return ""
    # Accounting parens: (123.45) -> negative
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    # Keep digits, '.', ',', and leading '-' only.
    s = re.sub(r"[^\d.,\-]", "", s)
    # Collapse any '-' that isn't a leading sign (shouldn't happen, but be safe).
    if s.count("-") > 1 or ("-" in s and not s.startswith("-")):
        s = ("-" if s.startswith("-") else "") + s.replace("-", "")
    if s in ("", "-", ".", "-.", ",", "-,"):
        return ""
    s = _normalize_numeric_string(s, decimal_sep)
    if s in ("", "-", ".", "-."):
        return ""
    try:
        n = float(s)
        if negative:
            n = -abs(n)
        return f"{n:.2f}"
    except ValueError:
        return ""


def _parse_float(value: str, decimal_sep: str = "auto") -> str:
    """Parse a fractional numeric value, preserving decimals.

    Used for fields like ``conversions`` where Google Ads exports
    fractional attribution (e.g. ``0.73``) — stripping decimals would
    turn 0.73 into 73 or 0. Returns '' for empty/missing values.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in ("--", "n/a", "nan", "null"):
        return ""
    # Accounting parens: (1.5) -> -1.5
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = re.sub(r"[^\d.,\-]", "", s)
    if s.count("-") > 1 or ("-" in s and not s.startswith("-")):
        s = ("-" if s.startswith("-") else "") + s.replace("-", "")
    if s in ("", "-", ".", "-.", ",", "-,"):
        return ""
    s = _normalize_numeric_string(s, decimal_sep)
    if s in ("", "-", ".", "-."):
        return ""
    try:
        n = float(s)
        if negative:
            n = -abs(n)
        # Drop trailing zeros / trailing dot for clean integer-like values.
        formatted = f"{n:.4f}".rstrip("0").rstrip(".")
        return formatted if formatted not in ("", "-") else "0"
    except ValueError:
        return ""


def _parse_int(value: str) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in ("--", "n/a", "nan", "null"):
        return ""
    s = re.sub(r"[^\d\-]", "", s)
    if s in ("", "-"):
        return ""
    try:
        return str(int(s))
    except ValueError:
        return ""


# Generic fallback formats, tried only when platform-canonical
# formats fail and the input isn't ambiguous slash-separated.
GENERIC_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%b %d, %Y",
    "%B %d, %Y",
    "%Y%m%d",
)


def _is_ambiguous_slash_date(s: str) -> bool:
    """True for slash-separated dates where both leading parts <= 12.

    Examples:
      - ``05/06/2026`` could be May 6 or June 5 (ambiguous).
      - ``05/06/26``  same ambiguity, just with a 2-digit year.
      - ``13/06/2026`` is unambiguous (day-first; 13 > 12).
      - ``2026/05/06`` is unambiguous (year-first).
    """
    m = re.match(r"^(\d{1,4})/(\d{1,4})/(\d{1,4})$", s)
    if not m:
        return False
    a, b, c = m.group(1), m.group(2), m.group(3)
    # Year-first (2026/05/06): not ambiguous.
    if len(a) == 4:
        return False
    # Trailing year must be 2- or 4-digit. Reject anything else (e.g. 1/1/1).
    if len(c) not in (2, 4):
        return False
    return int(a) <= 12 and int(b) <= 12


def _nonneg_int(value: str) -> int:
    """argparse ``type=`` validator: non-negative int.

    Rejects negative values (e.g. ``--skip-rows -1`` from a typo) at
    CLI parse time with a clear error, instead of letting them fall
    through to the auto-sniff path because the explicit-skip branch
    requires ``>= 0``.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(
            f"expected a non-negative integer, got {value!r}"
        )
    if n < 0:
        raise argparse.ArgumentTypeError(
            f"must be a non-negative integer, got {n}"
        )
    return n


def _validate_date_format(fmt: str) -> None:
    """Validate a strptime format string at CLI parse time.

    Raises ValueError if the format contains an invalid directive
    (e.g. ``%Q``) or cannot round-trip a sentinel date. We do this up
    front so a bad ``--date-format`` fails loudly before any rows are
    read, instead of being swallowed by per-row ValueError handlers.

    The validation does two checks:
      1. ``strftime`` on a sentinel date — catches truly invalid
         directives like ``%Q``.
      2. ``strptime`` round-trip on the formatted output — catches
         partial-format strings that strftime accepts but strptime
         can't parse (rare but possible).

    The sentinel is tz-aware (UTC) so timezone directives like
    ``%z``/``%Z`` render to a non-empty string and round-trip
    cleanly. A naive sentinel would make ``%z`` strftime to '' and
    fail the strptime round-trip, falsely rejecting a valid format.
    """
    sentinel = datetime(2026, 12, 31, tzinfo=timezone.utc)
    try:
        rendered = sentinel.strftime(fmt)
    except (ValueError, TypeError) as e:
        raise ValueError(str(e))
    # Some directives (e.g. %j) won't round-trip on an arbitrary date,
    # but the strftime check is the primary gate. Best-effort round trip:
    try:
        datetime.strptime(rendered, fmt)
    except ValueError as e:
        raise ValueError(f"format does not round-trip: {e}")


def _parse_date(
    value: str,
    platform: str | None = None,
    date_format: str | None = None,
) -> str:
    """Parse a date string to ISO ``YYYY-MM-DD``.

    Resolution order:
      1. If ``date_format`` is given, it takes precedence. On match, return.
         On mismatch, raise ValueError — do NOT silently fall through to
         other formats. The user told us how to read this column.
      2. ISO ``%Y-%m-%d`` (unambiguous; what most platforms export).
      3. Platform-canonical formats from the profile.
      4. Generic fallbacks (excluding the slash-ambiguous ones).
      5. If the input is slash-separated AND ambiguous (both leading
         parts <= 12), raise ValueError — caller should ask the user
         for --date-format.
      6. ISO prefix regex (last resort).
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""

    # If the user explicitly passed --date-format, honor it strictly.
    # A mismatch here is a data error, not a cue to guess.
    if date_format:
        try:
            return datetime.strptime(s, date_format).strftime("%Y-%m-%d")
        except ValueError as e:
            raise ValueError(
                f"date {s!r} did not match --date-format {date_format!r}: {e}"
            ) from None

    # Slash-ambiguity gate (Codex round 5): if the value is slash-separated
    # and ambiguous (both leading parts <= 12) AND the user gave no
    # --date-format, refuse to guess BEFORE trying any platform-canonical
    # format. Otherwise LinkedIn's "%m/%d/%Y" fallback would silently
    # parse "05/06/2026" as May 6, regressing the round-2 safeguard.
    # User-supplied --date-format above already wins; unambiguous slash
    # dates (e.g. 13/05/2026, day > 12) still flow into the platform
    # fallbacks below.
    if "/" in s and _is_ambiguous_slash_date(s):
        raise ValueError(
            f"Ambiguous slash-separated date {s!r}: cannot tell "
            f"month-first from day-first. Pass --date-format to disambiguate."
        )

    formats_to_try: list[str] = ["%Y-%m-%d"]
    if platform and platform in PROFILES:
        for fmt in PROFILES[platform].date_format:
            if fmt not in formats_to_try:
                formats_to_try.append(fmt)
    for fmt in GENERIC_DATE_FORMATS:
        if fmt not in formats_to_try:
            formats_to_try.append(fmt)

    for fmt in formats_to_try:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Non-ambiguous slash dates: try day-first then month-first.
    if "/" in s:
        for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d/%m/%y", "%m/%d/%y"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    # Last resort: ISO-ish prefix.
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    return s  # return as-is; downstream can flag it


def _conversion_value_or_null(raw: str, decimal_sep: str = "auto") -> str:
    """Conversion value is the one field where missing != 0.

    Per the schema doc: when the source has no column or the cell is
    blank, we emit empty (NULL) rather than '0.00' so analysis doesn't
    silently treat a missing column as zero revenue.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _parse_currency(s, decimal_sep)


def normalize_row(
    row: dict[str, str],
    profile: PlatformProfile,
    columns: dict[str, str | None],
    decimal_sep: str = "auto",
    date_format: str | None = None,
) -> dict[str, str]:
    def get(field: str) -> str:
        col = columns.get(field)
        if col is None:
            return ""
        return row.get(col, "") or ""

    return {
        "platform": profile.name,
        "date": _parse_date(get("date"), platform=profile.name, date_format=date_format),
        "campaign": get("campaign").strip(),
        "ad_set": get("ad_set").strip(),
        "ad": get("ad").strip(),
        "spend": _parse_currency(get("spend"), decimal_sep),
        "impressions": _parse_int(get("impressions")),
        "clicks": _parse_int(get("clicks")),
        "conversions": _parse_float(get("conversions"), decimal_sep),
        "conversion_value": _conversion_value_or_null(get("conversion_value"), decimal_sep),
    }


def normalize(
    reader: csv.DictReader,
    profile: PlatformProfile,
    decimal_sep: str = "auto",
    date_format: str | None = None,
) -> list[dict[str, str]]:
    headers = reader.fieldnames or []
    columns = {
        "date": _find_column(headers, profile.date),
        "campaign": _find_column(headers, profile.campaign),
        "ad_set": _find_column(headers, profile.ad_set),
        "ad": _find_column(headers, profile.ad),
        "spend": _find_column(headers, profile.spend),
        "impressions": _find_column(headers, profile.impressions),
        "clicks": _find_column(headers, profile.clicks),
        "conversions": _find_column(headers, profile.conversions),
        "conversion_value": _find_column(headers, profile.conversion_value),
    }
    out: list[dict[str, str]] = []
    for row in reader:
        # Skip totals/summary rows that some exports append. Different
        # platforms place the summary token in different columns —
        # Google Ads puts "Total: Account" in the campaign column with
        # a blank date — so we scan every cell. We anchor on whole-cell
        # equality or a starts-with match for known prefixes to avoid
        # dropping legitimate campaign names that contain the word
        # "total".
        if _is_totals_row(row):
            continue
        normalized = normalize_row(row, profile, columns, decimal_sep, date_format)
        if not normalized["campaign"] and not normalized["spend"]:
            continue
        out.append(normalized)
    return out


_TOTALS_EXACT = frozenset({
    "total",
    "totals",
    "grand total",
    "account total",
    "subtotal",
    "sub-total",
    "sub total",
})

_TOTALS_PREFIXES = (
    "total:",
    "totals:",
    "grand total:",
    "account total:",
    "total -",
    "totals -",
)


def _is_totals_row(row: dict[str, str]) -> bool:
    """Return True if any cell in the row looks like a summary token.

    Case-insensitive. Matches whole-cell values (e.g. ``Total``,
    ``Grand total``) or starts-with prefixes (e.g. ``Total: Account``,
    ``Total - All campaigns``) so we don't drop legitimate campaigns
    whose names merely include the word "total".
    """
    for raw in row.values():
        if not isinstance(raw, str):
            continue
        cell = raw.strip().lower()
        if not cell:
            continue
        if cell in _TOTALS_EXACT:
            return True
        if any(cell.startswith(p) for p in _TOTALS_PREFIXES):
            return True
    return False


def _all_platform_tokens() -> set[str]:
    """Every fingerprint and highly-specific token across all platforms.

    Used to score candidate header lines when looking for a buried
    header row beneath title/filter preamble.
    """
    tokens: set[str] = set()
    for profile in PROFILES.values():
        tokens.update(profile.fingerprint)
    for specific in HIGHLY_SPECIFIC_FINGERPRINTS.values():
        tokens.update(specific)
    return tokens


def _all_highly_specific_tokens() -> set[str]:
    """Union of every platform's highly-specific fingerprint tokens.

    Used to score candidate header lines: a single hit from this set
    is enough to claim the line as the header, because these tokens
    essentially only appear in one platform's export.
    """
    tokens: set[str] = set()
    for specific in HIGHLY_SPECIFIC_FINGERPRINTS.values():
        tokens.update(specific)
    return tokens


def _score_header_candidate(
    line: str,
    generic_tokens: set[str],
    specific_tokens: set[str],
) -> tuple[bool, int]:
    """Score a candidate header line.

    Returns ``(highly_specific_hit, generic_distinct)`` where:
      * ``highly_specific_hit`` is True iff any cell matches a token
        from ``specific_tokens`` (the union of every platform's
        ``HIGHLY_SPECIFIC_FINGERPRINTS``). A single such hit is
        sufficient on its own — these tokens are pathognomonic.
      * ``generic_distinct`` is the count of distinct generic
        fingerprint tokens (across all platforms, deduped) present
        in the row's cells. ``_find_header_row`` requires ``>= 2``
        for the generic-token path, paired with a structural
        plausibility pre-filter that independently rejects the
        narrow preamble rows (``"Campaign,Cost"``) and metadata
        preambles (``"Date range: ...","Impressions: 12345"``) that
        previously fooled a pure token-count rule.

    Uses csv.reader on the single line so quoted commas are handled.
    Token comparisons are case-insensitive and whitespace-collapsed
    (via ``_norm_header``), matching the existing normalization.
    """
    if not line.strip():
        return (False, 0)
    try:
        cells = next(csv.reader([line]))
    except (csv.Error, StopIteration):
        return (False, 0)
    specific_hit = False
    generic_matched: set[str] = set()
    for cell in cells:
        normalized = _norm_header(cell)
        if not normalized:
            continue
        if normalized in specific_tokens:
            specific_hit = True
        if normalized in generic_tokens:
            generic_matched.add(normalized)
    return (specific_hit, len(generic_matched))


def _count_header_matches(line: str, tokens: set[str]) -> int:
    """Count distinct generic-fingerprint matches on a line.

    Retained for backward compatibility and direct testing. Prefer
    ``_score_header_candidate`` for the full weighted score. Counts
    distinct matched tokens (not raw cell hits) so a junk preamble
    row like ``Campaign,Campaign`` can't pad its score by repeating
    the same token.
    """
    _, generic = _score_header_candidate(line, tokens, set())
    return generic


_DATE_HEADER_RE = re.compile(
    r"^(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2}(?:\d{2})?|\d{8})$"
)
_NUMERIC_STRIP_RE = re.compile(r"[\s$,.\-()]")


def _looks_like_header_row(cells: list[str], allow_narrow: bool = False) -> bool:
    """Structural plausibility check for a CSV row being a header.

    Codex round-7 added this guard in front of the existing token-based
    tier logic. It rejects rows that look structurally like a preamble
    or data row regardless of which fingerprint tokens they happen to
    contain. A real header row has multiple short, non-numeric, non-date
    cells; any failure below means this is not a header:

      * Fewer than 3 non-empty cells — too narrow to be a header.
        Codex round-8 carve-out: when ``allow_narrow=True`` (caller
        has independently confirmed the row contains a highly-specific
        token), this check is skipped. Highly-specific tokens like
        ``Impr.`` or ``Stat Time Day`` are platform-unique and don't
        appear in preamble metadata, so a 2-column export like
        ``"Impr.","Cost"`` is overwhelmingly a real header. All other
        structural guards below STILL apply.
      * Any cell that's purely numeric after stripping currency,
        thousands, decimal, paren-negative, and whitespace noise.
        Real headers don't have ``"1234"`` as a column name.
      * Any cell that parses as a date (ISO ``YYYY-MM-DD``, slash
        ``M/D/Y`` or ``M/D/YY``, compact ``YYYYMMDD``). A date cell
        signals a data row that happens to share a token with a
        header (e.g. ``"2026-01-01","2026-05-01","Impr."``).
      * Any cell longer than 80 characters — preamble prose like
        ``"Date range: 2026-01-01 to 2026-05-01"`` blows past this
        bound but a real header cell never does.
      * Any cell containing ``":"`` — colons in real headers are
        vanishingly rare; ``"Date range:"`` / ``"Impressions: 12345"``
        metadata prose is the dominant case, so this is a cheap
        decisive guard against metadata-preamble false-positives.

    Returns False on any failure, True otherwise.
    """
    non_empty = [c for c in cells if c and c.strip()]
    if not allow_narrow and len(non_empty) < 3:
        return False
    if not non_empty:
        # Even with allow_narrow, an empty row isn't a header.
        return False
    for cell in non_empty:
        stripped = cell.strip()
        if ":" in stripped:
            return False
        if len(stripped) > 80:
            return False
        if _DATE_HEADER_RE.match(stripped):
            return False
        # Strip currency/grouping/paren-negative/whitespace noise. If
        # what remains is all digits (or empty), this cell is numeric.
        numeric_residue = _NUMERIC_STRIP_RE.sub("", stripped)
        if numeric_residue and numeric_residue.isdigit():
            return False
    return True


def _find_header_row(lines: list[str], tokens: set[str]) -> int:
    """Index of the line that best qualifies as a header row.

    Layered design (Codex round 7):

    0. **Structural pre-filter** (``_looks_like_header_row``). Before
       any token scoring, every candidate row must pass a structural
       plausibility check: at least 3 non-empty cells, no purely
       numeric cells, no date-shaped cells, no cells longer than 80
       characters, no cells containing ``":"``. This single filter
       kills the dominant metadata-preamble false-positive
       (``"Date range: ...","Impressions: 12345"``) regardless of
       which fingerprint tokens it contains.

       **Codex round-8 carve-out:** a candidate row with fewer than
       3 non-empty cells is allowed through the structural filter IF
       it contains at least one highly-specific token. All other
       structural guards (numeric, date, length, colon) still apply.
       Highly-specific tokens (``Impr.``, ``Stat Time Day``, etc.)
       are platform-unique and don't appear in preamble metadata, so
       a 2-column export like ``"Impr.","Cost"`` is overwhelmingly a
       real header — but a generic-only narrow row like
       ``"Campaign","Cost"`` does NOT get the carve-out (the round-6
       protection still holds).

    1. **Highly-specific token wins.** Among rows that pass the
       structural filter, if any contains a highly-specific token
       (e.g. TikTok's ``Stat Time Day``, Google's ``Impr.``, GA4's
       ``Session campaign``, LinkedIn's ``Start Date (in UTC)``,
       Meta's ``Amount Spent (USD)``), return the FIRST such row
       immediately. Highly-specific tokens are platform-unique, so a
       single hit is decisive.

    2. **Otherwise, ``>= 2`` distinct generic fingerprint tokens.**
       Among structurally-plausible rows, pick the one with the most
       distinct generic matches; ties go to the earliest. Dropping
       the bar back from 3 to 2 (relative to round 6) is safe because
       the structural filter independently rejects the 2-cell
       ``"Campaign,Cost"`` preamble that motivated the round-6 bump,
       AND it lets in legitimate headers like Google's
       ``"Day,Campaign,Cost"`` that only score 2 generic hits when
       ``Impr.`` is spelled out as ``Impressions``.

    Returns 0 if no line qualifies (backward compatible: treat row 0
    as the header so downstream platform detection runs and emits a
    clean error if the file really has no header).
    """
    specific = _all_highly_specific_tokens()
    best_idx = -1
    best_score = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            cells = next(csv.reader([line]))
        except (csv.Error, StopIteration):
            continue
        # Score first so we know whether this row has a highly-specific
        # token; that determines whether the structural filter can
        # tolerate a narrow (<3 cell) row. The carve-out is tier-1 only:
        # generic-only narrow rows like "Campaign,Cost" still fail.
        highly_specific_hit, generic_distinct = _score_header_candidate(
            line, tokens, specific
        )
        # Structural pre-filter — reject preamble/metadata/data rows
        # before they get a chance to win on token score alone. The
        # narrow-cell carve-out only applies when a highly-specific
        # token is present; all other structural guards (numeric, date,
        # length, colon) still fire either way.
        if not _looks_like_header_row(cells, allow_narrow=highly_specific_hit):
            continue
        # Tier 1: highly-specific wins. Return first such line
        # immediately — these tokens are platform-unique and a single
        # hit beats any generic-only candidate by precedence.
        if highly_specific_hit:
            return i
        # Tier 2: track best-by-distinct-matches among rows meeting
        # the >=2 generic threshold. Strict ``>`` so the earliest row
        # wins ties (matches the round-3 contract that earlier rows
        # are preferred when scores are equal).
        if generic_distinct >= 2 and generic_distinct > best_score:
            best_idx = i
            best_score = generic_distinct
    if best_idx >= 0:
        return best_idx
    return 0


def _open_input(path: str) -> IO[str]:
    if path == "-":
        return sys.stdin
    return open(path, "r", encoding="utf-8-sig", newline="")


def _open_output(path: str | None) -> IO[str]:
    if not path:
        return sys.stdout
    return open(path, "w", encoding="utf-8", newline="")


def _stream_with_skipped_rows(in_fh: IO[str], skip_rows: int | None, max_scan: int = 15) -> IO[str]:
    """Return a stream positioned past any preamble rows.

    If ``skip_rows`` is given (an explicit user contract), skip exactly
    that many lines — drawing additional lines from the stream if the
    scan buffer isn't deep enough. ``--skip-rows 0`` is a valid no-op.

    Otherwise (auto-sniff), buffer up to ``max_scan`` lines from the
    head of the input and use platform-token heuristics to locate the
    header row. The auto-sniff path is intentionally capped at the
    scan window because it's a heuristic, not a contract.

    Lines before the header are discarded; everything from the header
    onward (including the buffered tail) is replayed via chained
    iterators so csv.DictReader sees a clean stream.

    For file inputs this could use seek(), but stdin can't seek — so
    we always buffer-and-replay for uniformity.
    """
    tokens = _all_platform_tokens()

    if skip_rows is not None and skip_rows >= 0:
        # Explicit user contract: skip exactly N lines, pulling more
        # from the stream if needed. Never silently cap.
        consumed = 0
        while consumed < skip_rows:
            line = in_fh.readline()
            if not line:
                break  # EOF before we hit N — tail will be empty
            consumed += 1
        # Nothing buffered; csv.DictReader reads directly from in_fh.
        return _ConcatTextIO([], in_fh)

    # Auto-sniff path: buffer the scan window and heuristically locate
    # the header row.
    buffer: list[str] = []
    for _ in range(max_scan):
        line = in_fh.readline()
        if not line:
            break
        buffer.append(line)

    header_idx = _find_header_row(buffer, tokens)
    tail = buffer[header_idx:]
    # Build a stream that yields the tail followed by the rest of the original input.
    return _ConcatTextIO(tail, in_fh)


class _ConcatTextIO(io.TextIOBase):
    """Stitch a list of already-read lines onto the front of a stream.

    csv.DictReader iterates the file line-by-line, so it only needs
    __iter__. We implement readline/__iter__ explicitly; everything
    else falls through to the underlying stream.
    """

    def __init__(self, head_lines: list[str], rest: IO[str]) -> None:
        super().__init__()
        self._head = iter(head_lines)
        self._rest = rest
        self._head_done = False

    def readable(self) -> bool:
        return True

    def readline(self, size: int = -1) -> str:  # type: ignore[override]
        if not self._head_done:
            try:
                return next(self._head)
            except StopIteration:
                self._head_done = True
        return self._rest.readline()

    def __iter__(self):
        return self

    def __next__(self) -> str:
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def close(self) -> None:
        if self._rest is not sys.stdin:
            try:
                self._rest.close()
            except Exception:
                pass
        super().close()


# ---------------------------------------------------------------------------
# Smoke / self-test
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """Inline assertions for parser primitives.

    Run with ``python3 parse_csv.py --self-test``. Exits 0 on success,
    1 on first failure. These do NOT run on every parse call.
    """
    failures: list[str] = []

    def check(label: str, got, want) -> None:
        if got != want:
            failures.append(f"{label}: got {got!r}, want {want!r}")

    # Fix A — currency / decimal-separator
    check("US $1,234.56", _parse_currency("$1,234.56"), "1234.56")
    check("EU 1.234,56", _parse_currency("1.234,56"), "1234.56")
    check("EU bare 1234,56", _parse_currency("1234,56"), "1234.56")
    check("US thousands 1,234", _parse_currency("1,234"), "1234.00")
    check("EU bare 123,45", _parse_currency("123,45"), "123.45")
    check("Parens (123.45)", _parse_currency("(123.45)"), "-123.45")
    check("Signed EU -1.234,56", _parse_currency("-1.234,56"), "-1234.56")
    check("Empty", _parse_currency(""), "")
    check("Forced comma sep 1.234", _parse_currency("1.234", decimal_sep="comma"), "1234.00")
    check("Forced period sep 1,234", _parse_currency("1,234", decimal_sep="period"), "1234.00")
    check("Float frac 0.73", _parse_float("0.73"), "0.73")
    check("Float EU 0,73", _parse_float("0,73"), "0.73")

    # Fix H (Codex round 4) — single-digit comma decimals must parse as
    # decimal, not get swallowed as thousands. Reasoning lives in
    # _detect_decimal_separator's docstring; verify edge cases here.
    check("Single-digit comma 0,5", _parse_currency("0,5", "auto"), "0.50")
    check("Single-digit comma 1,2", _parse_currency("1,2", "auto"), "1.20")
    check("Two-digit comma 123,45", _parse_currency("123,45", "auto"), "123.45")
    check("Three-digit comma 1,234 stays US thousands", _parse_currency("1,234", "auto"), "1234.00")
    # 4+ digits after a single comma: thousands groups are always exactly
    # 3 digits, so this must be a decimal. 1,2345 -> 1.2345 (rounded to
    # 2dp by _parse_currency).
    check("Four-digit comma 1,2345 -> decimal", _parse_currency("1,2345", "auto"), "1.23")
    check("Four-digit comma _parse_float 1,2345 -> decimal", _parse_float("1,2345", "auto"), "1.2345")

    # Fix B — detect_platform with only highly-specific token
    check(
        "Detect TikTok via stat time day",
        detect_platform(["Stat Time Day", "Some Random Column"]),
        "tiktok",
    )
    check(
        "Detect GA4 via session campaign",
        detect_platform(["Session Campaign", "Foo"]),
        "ga4",
    )
    check(
        "Detect LinkedIn via start date (in utc)",
        detect_platform(["Start Date (in UTC)", "Foo"]),
        "linkedin",
    )
    check(
        "Detect Google via impr.",
        detect_platform(["Impr.", "Foo"]),
        "google",
    )
    # Existing 2-token detection still works
    check(
        "Detect Meta via fingerprint",
        detect_platform(["Campaign Name", "Reach", "Other"]),
        "meta",
    )
    # No platform claim
    check(
        "Unknown headers return None",
        detect_platform(["Foo", "Bar", "Baz"]),
        None,
    )

    # Fix C — header-row sniffer
    preamble = [
        '"Google Ads Report",,,\n',
        '"Date range: 2026-04-01 to 2026-05-01",,,\n',
        ',,,\n',
        'Day,Campaign,Cost,Clicks,Impr.,Conversions\n',
        '2026-04-01,Brand Search,12.34,45,1000,0.73\n',
    ]
    tokens = _all_platform_tokens()
    check("Find header row past preamble", _find_header_row(preamble, tokens), 3)
    check(
        "No preamble => header row 0",
        _find_header_row(['Day,Campaign,Cost,Clicks,Impr.\n', 'data\n'], tokens),
        0,
    )

    # Fix D — date parsing
    check("ISO date", _parse_date("2026-05-06"), "2026-05-06")
    check(
        "GA4 compact date",
        _parse_date("20260506", platform="ga4"),
        "2026-05-06",
    )
    check(
        "LinkedIn slash date",
        _parse_date("05/06/2026", platform="linkedin", date_format="%m/%d/%Y"),
        "2026-05-06",
    )
    # Ambiguous slash with no hints should raise — 4-digit year.
    try:
        _parse_date("05/06/2026")
    except ValueError:
        pass
    else:
        failures.append("Ambiguous slash date should raise without hints")
    # Ambiguous slash with no hints should raise — 2-digit year (Codex round 3).
    try:
        _parse_date("05/06/26")
    except ValueError:
        pass
    else:
        failures.append("Ambiguous 2-digit-year slash date should raise without hints")
    # Unambiguous day-first should parse without --date-format.
    check("Day-first 13/06/2026", _parse_date("13/06/2026"), "2026-06-13")

    # Fix K (Codex round 5) — ambiguity gate must fire BEFORE platform
    # canonical formats. LinkedIn has "%m/%d/%Y" in its date_format list,
    # which previously silently parsed "05/06/2026" as May 6 when called
    # with platform="linkedin" and no --date-format. Now the slash
    # ambiguity check runs first and raises.
    try:
        _parse_date("05/06/2026", platform="linkedin", date_format=None)
    except ValueError:
        pass
    else:
        failures.append(
            "Ambiguous LinkedIn slash date 05/06/2026 must raise without --date-format"
        )
    # Unambiguous day-first slash date on LinkedIn (day > 12) still
    # flows through to the day-first fallback.
    check(
        "LinkedIn unambiguous 13/05/2026",
        _parse_date("13/05/2026", platform="linkedin", date_format=None),
        "2026-05-13",
    )
    # User-supplied --date-format always wins, even on a slash date that
    # would otherwise be ambiguous.
    check(
        "LinkedIn 05/06/2026 with explicit --date-format %m/%d/%Y",
        _parse_date("05/06/2026", platform="linkedin", date_format="%m/%d/%Y"),
        "2026-05-06",
    )

    # Fix L (Codex round 5) — argparse --skip-rows must reject negatives
    # at parse time with a clear error.
    parser_under_test = argparse.ArgumentParser()
    parser_under_test.add_argument("--skip-rows", type=_nonneg_int, default=None)
    try:
        parser_under_test.parse_args(["--skip-rows", "-1"])
    except SystemExit:
        # argparse exits on type validation failure — expected.
        pass
    else:
        failures.append("--skip-rows -1 must fail argparse validation")
    # Direct validator unit-check too.
    try:
        _nonneg_int("-1")
    except argparse.ArgumentTypeError:
        pass
    else:
        failures.append("_nonneg_int('-1') must raise ArgumentTypeError")
    # Sanity: a valid non-negative integer still parses through.
    check("_nonneg_int('0')", _nonneg_int("0"), 0)
    check("_nonneg_int('20')", _nonneg_int("20"), 20)

    # Fix E (Codex round 3) — invalid --date-format must be caught up front.
    try:
        _validate_date_format("%Q/%d/%Y")
    except ValueError:
        pass
    else:
        failures.append("Invalid --date-format %Q/%d/%Y should raise ValueError")
    # Valid format should pass validation cleanly.
    try:
        _validate_date_format("%m/%d/%Y")
    except ValueError as e:
        failures.append(f"Valid --date-format %m/%d/%Y should not raise: {e}")

    # Fix I (Codex round 4) — timezone directives must pass validation.
    # Previously the naive sentinel made strftime('%z') return '' and the
    # strptime round-trip then failed, falsely rejecting a valid format.
    try:
        _validate_date_format("%Y-%m-%d %z")
    except ValueError as e:
        failures.append(f"Valid --date-format with %z should not raise: {e}")
    # And the invalid-directive check still rejects garbage like %Q.
    try:
        _validate_date_format("%Q/%d/%Y")
    except ValueError:
        pass
    else:
        failures.append("After tz fix, invalid %Q should still raise")

    # Fix J (Codex round 4) — _count_header_matches counts DISTINCT tokens.
    # A preamble row like "Campaign,Campaign" shouldn't claim header
    # status by repeating the same token; we should still find the real
    # header row beneath it.
    tokens_j = _all_platform_tokens()
    repeated_preamble = [
        'Campaign,Campaign\n',
        'Day,Campaign,Cost,Clicks,Impr.,Conversions\n',
        '2026-04-01,Brand Search,12.34,45,1000,0.73\n',
    ]
    if _count_header_matches('Campaign,Campaign\n', tokens_j) >= 2:
        failures.append(
            "Repeated single token 'Campaign,Campaign' must not count as >=2 matches"
        )
    check(
        "Real header beats repeated-token preamble",
        _find_header_row(repeated_preamble, tokens_j),
        1,
    )

    # Fix M (Codex round 6) — weighted header sniff. The old >=2 threshold
    # was wrong in two opposite directions on the same line of code:
    #   * Too WEAK: a preamble row like "Campaign,Cost" hits 2 generic
    #     Google tokens and stole the header from the real
    #     "Day,Campaign,Cost,Clicks,Impr." row below it.
    #   * Too STRICT: a real TikTok header whose only recognized token
    #     is the highly-specific "Stat Time Day" scored 1 and was
    #     skipped, even though "Stat Time Day" is pathognomonic.
    # New rule: highly-specific token => instant claim; otherwise need
    # >=3 distinct generic tokens.
    tokens_m = _all_platform_tokens()
    # Preamble "Campaign,Cost" (2 generic hits, no highly-specific) must
    # NOT claim the header when a richer real header sits below.
    weak_preamble = [
        'Campaign,Cost\n',
        'Day,Campaign,Cost,Clicks,Impr.\n',
        '2026-04-01,Brand Search,12.34,45,1000\n',
    ]
    check(
        "Two-generic preamble loses to real header below",
        _find_header_row(weak_preamble, tokens_m),
        1,
    )
    # A TikTok-style header with one highly-specific token (Stat Time Day)
    # and otherwise unknown columns must still qualify.
    tiktok_buried = [
        '"Report","2026-05-21"\n',
        'Stat Time Day,UnknownA,UnknownB\n',
        '2026-05-20,foo,bar\n',
    ]
    check(
        "Highly-specific single-token header qualifies",
        _find_header_row(tiktok_buried, tokens_m),
        1,
    )
    # The round-4 repeated-token case: "Campaign,Campaign" alone is the
    # only line. Distinct generic = 1, no highly-specific. Falls back to
    # 0 (the documented contract when nothing qualifies); downstream
    # platform detection will then error cleanly because there aren't
    # enough fingerprint hits to identify a platform.
    check(
        "Lone repeated-token line falls back to 0",
        _find_header_row(['Campaign,Campaign\n'], tokens_m),
        0,
    )
    # Regression: a normal Google header on line 0 with the canonical
    # "Impr." spelling qualifies on the highly-specific path.
    check(
        "Google header at line 0 with Impr. returns 0",
        _find_header_row(['Day,Campaign,Cost,Clicks,Impr.\n', 'data\n'], tokens_m),
        0,
    )
    # Regression: 5 lines of preamble + a Google header at line 5
    # (highly-specific Impr. token) returns 5.
    preamble_5 = [
        '"Google Ads Report"\n',
        '"Account: Foo"\n',
        '"Date range: ..."\n',
        '"Filter: All"\n',
        ',,,\n',
        'Day,Campaign,Cost,Clicks,Impr.\n',
        '2026-04-01,Brand Search,12.34,45,1000\n',
    ]
    check(
        "Header at line 5 past 5-line preamble",
        _find_header_row(preamble_5, tokens_m),
        5,
    )
    # The new generic-token threshold is exactly 3 distinct tokens.
    # Boundary: a line with 2 distinct generic tokens does NOT qualify.
    check(
        "Two distinct generic tokens does not qualify",
        _score_header_candidate(
            'Campaign,Cost\n', tokens_m, _all_highly_specific_tokens()
        ),
        (False, 2),
    )
    # And 3 distinct generic tokens DOES qualify (no highly-specific).
    # Pick three tokens that are all in generic fingerprints but none
    # of which are in HIGHLY_SPECIFIC_FINGERPRINTS: "campaign name",
    # "cost", "reach" -> 3 generics, 0 specific.
    specific_m = _all_highly_specific_tokens()
    sample_three = _score_header_candidate(
        'Campaign Name,Cost,Reach\n', tokens_m, specific_m
    )
    if sample_three[0]:
        failures.append(
            f"Sample three-generic line should not hit highly-specific: {sample_three!r}"
        )
    if sample_three[1] < 3:
        failures.append(
            f"Sample three-generic line should have >=3 generic hits: {sample_three!r}"
        )

    # Fix N (Codex round 7) — structural pre-filter + generic threshold
    # dropped back to 2. The combination handles two opposite failure
    # modes that the round-6 ``>= 3`` rule alone couldn't:
    #   * P1 (too strict): a real Google header where ``Impr.`` is
    #     spelled out as ``Impressions`` only contributes 2 generic
    #     fingerprint hits (Campaign + Cost), so round-6 would fall
    #     back to row 0. Now ``>= 2`` is enough, but only for rows
    #     that pass the structural plausibility check.
    #   * P2 (too eager): a metadata preamble like
    #     ``"Date range: ...","Impressions: 12345"`` contained
    #     ``Impressions`` and won tier-1 instantly. Structural filter
    #     rejects it now: 2 cells, both contain colons, one is too
    #     long, one is numeric after stripping.
    tokens_n = _all_platform_tokens()

    # Tier-1 metadata-preamble guard. Row 0 has colons / numeric cell
    # / only 2 cells — structural ✗. Row 1 has 5 cells, no numbers, no
    # colons, and >=2 generic tokens — passes structural, then tier-2.
    metadata_preamble = [
        'Date range: 2026-01-01 to 2026-05-01,Impressions: 12345\n',
        'Day,Campaign,Cost,Clicks,Impressions\n',
    ]
    check(
        "Tier-1 metadata preamble guard (colon + numeric)",
        _find_header_row(metadata_preamble, tokens_n),
        1,
    )
    # Directly assert row 0 fails structural so a future refactor that
    # accidentally loosens the filter is caught.
    if _looks_like_header_row(
        [
            "Date range: 2026-01-01 to 2026-05-01",
            "Impressions: 12345",
        ]
    ):
        failures.append(
            "Metadata preamble row with colons must fail structural pre-filter"
        )

    # Tier-2 dropped-to-2 success. No highly-specific match anywhere;
    # the real header has exactly 2 generic hits (Campaign + Cost) and
    # 3 cells. Row 0 is a 2-cell title row — fails structural on cell
    # count.
    two_generic_real = [
        'Title row metadata,\n',
        'Campaign,Cost,Random Custom Column\n',
    ]
    check(
        "Tier-2 with >=2 distinct generic tokens qualifies",
        _find_header_row(two_generic_real, tokens_n),
        1,
    )

    # Pure-numeric preamble guard. Row 0 is all numeric — fails
    # structural even though it has 3 cells.
    numeric_preamble = [
        '1234,5678,9012\n',
        'Day,Campaign,Cost,Clicks\n',
    ]
    check(
        "Pure-numeric preamble fails structural",
        _find_header_row(numeric_preamble, tokens_n),
        1,
    )
    if _looks_like_header_row(["1234", "5678", "9012"]):
        failures.append("All-numeric row must fail structural pre-filter")

    # Date-cell preamble guard. Row 0 has ISO dates and the
    # highly-specific token ``Impr.`` — without structural filtering
    # this would have won tier-1. Now it fails structural on the date
    # cells.
    date_preamble = [
        '2026-01-01,2026-05-01,Impr.\n',
        'Day,Campaign,Cost,Impr.\n',
    ]
    check(
        "Date-cell preamble fails structural even with highly-specific token",
        _find_header_row(date_preamble, tokens_n),
        1,
    )
    if _looks_like_header_row(["2026-01-01", "2026-05-01", "Impr."]):
        failures.append("Date-cell row must fail structural pre-filter")

    # Fix O (Codex round 8) — narrow-header carve-out for highly-specific
    # tokens. A 2-column export like ``"Impr.","Cost"`` is overwhelmingly
    # a real header, not a preamble line, because highly-specific tokens
    # are platform-unique by definition. The carve-out relaxes ONLY the
    # ``< 3 non-empty cells`` guard; numeric/date/colon/length guards
    # still fire. And the carve-out is tier-1 only — a generic-only
    # narrow row like ``"Campaign","Cost"`` still fails (round-6).

    # O.1: narrow row with a highly-specific token wins. Row 0 has
    # 2 cells and no highly-specific token — fails structural (narrow,
    # no carve-out). Row 1 has 2 cells but contains ``Impr.`` — gets
    # the carve-out, wins tier-1.
    narrow_specific_wins = [
        'Report metadata,v1.0\n',
        'Impr.,Cost\n',
    ]
    check(
        "Narrow row with highly-specific token wins via carve-out",
        _find_header_row(narrow_specific_wins, tokens_n),
        1,
    )

    # O.2: narrow row WITHOUT highly-specific token still rejected.
    # ``"Campaign,Cost"`` is the round-6 case — 2 generic tokens, no
    # highly-specific, only 2 cells. Must still fail structural and
    # fall through to row 1.
    narrow_generic_rejected = [
        'Campaign,Cost\n',
        'Day,Campaign,Cost,Clicks,Impr.\n',
    ]
    check(
        "Narrow generic-only row still rejected (round-6 protection holds)",
        _find_header_row(narrow_generic_rejected, tokens_n),
        1,
    )
    # Directly assert the narrow-generic row fails structural without
    # the carve-out flag, confirming the round-6 protection.
    if _looks_like_header_row(["Campaign", "Cost"], allow_narrow=False):
        failures.append(
            "Narrow generic-only row must fail structural without carve-out"
        )

    # O.3: narrow row with highly-specific token BUT colons still
    # rejected. The carve-out only relaxes the cell-count guard;
    # numeric/date/colon/length guards still fire even when a
    # highly-specific token is present.
    narrow_specific_with_colon = [
        'Impr.: 12345,Cost: 67\n',
        'Day,Campaign,Cost,Impr.\n',
    ]
    check(
        "Narrow row with highly-specific token + colon still rejected",
        _find_header_row(narrow_specific_with_colon, tokens_n),
        1,
    )
    # Directly assert: even with allow_narrow=True, colon-containing
    # cells fail. Guards stacking on top of the carve-out is the
    # invariant we want to lock in.
    if _looks_like_header_row(
        ["Impr.: 12345", "Cost: 67"], allow_narrow=True
    ):
        failures.append(
            "Narrow row with colons must fail even with allow_narrow=True"
        )

    # Fix F (Codex round 3) — user --date-format takes precedence; mismatch
    # is a data error, not a cue to fall through to other formats.
    try:
        _parse_date("2026-05-06", date_format="%m/%d/%Y")
    except ValueError:
        pass
    else:
        failures.append(
            "Cell that doesn't match user --date-format should raise, not silently parse"
        )

    # Fix G (Codex round 3) — _stream_with_skipped_rows must skip exactly N
    # lines even when N exceeds the auto-scan window (default 15).
    preamble_20 = "\n".join(f"# preamble line {i}" for i in range(20)) + "\n"
    header_row = "date,campaign,cost,clicks,impressions,conversions\n"
    data_row = "2026-04-01,Brand Search,12.34,45,1000,0.73\n"
    fixture = io.StringIO(preamble_20 + header_row + data_row)
    stream = _stream_with_skipped_rows(fixture, skip_rows=20)
    reader = csv.DictReader(stream)
    out_rows = list(reader)
    if reader.fieldnames != ["date", "campaign", "cost", "clicks", "impressions", "conversions"]:
        failures.append(
            f"--skip-rows 20 past 15-line scan window: wrong header "
            f"{reader.fieldnames!r}"
        )
    if len(out_rows) != 1:
        failures.append(
            f"--skip-rows 20 past 15-line scan window: got {len(out_rows)} rows, want 1"
        )

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"{len(failures)} self-test failures", file=sys.stderr)
        return 1
    print("self-test OK", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize a Google Ads, Meta, TikTok, LinkedIn, or GA4 CSV export "
            "to a single ad-performance schema."
        )
    )
    parser.add_argument("input", nargs="?", help="Path to input CSV. Use '-' for stdin.")
    parser.add_argument(
        "--platform",
        choices=PLATFORMS,
        help="Override platform detection. If omitted, the platform is inferred from headers.",
    )
    parser.add_argument(
        "--out",
        help="Path to output CSV. Defaults to stdout.",
    )
    parser.add_argument(
        "--decimal-sep",
        choices=DECIMAL_SEP_CHOICES,
        default="auto",
        help=(
            "Decimal separator convention for numeric fields. "
            "'auto' (default) heuristically detects US (1,234.56) vs European (1.234,56) formats. "
            "'period' forces '.' as decimal / ',' as thousands. "
            "'comma' forces ',' as decimal / '.' as thousands."
        ),
    )
    parser.add_argument(
        "--skip-rows",
        type=_nonneg_int,
        default=None,
        help=(
            "Skip exactly N lines before the CSV header. N must be a "
            "non-negative integer and is not capped — if your preamble is "
            "20 lines, pass --skip-rows 20. If omitted, the parser sniffs "
            "the first 15 lines and locates the header row by matching "
            "cells against known platform tokens — useful for Google Ads "
            "/ similar UI exports that include title and filter rows "
            "before the header."
        ),
    )
    parser.add_argument(
        "--date-format",
        help=(
            "strptime-format string for the date column (e.g. '%%m/%%d/%%Y'). "
            "Required when dates are slash-separated and ambiguous between "
            "month-first and day-first (e.g. 05/06/2026)."
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run inline assertions over parser primitives and exit.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    if not args.input:
        parser.error("the following arguments are required: input (or pass --self-test)")

    # Validate --date-format up front so a bad directive (e.g. %Q) fails
    # loudly here instead of being silently swallowed by per-row ValueError
    # handlers and falling through to other formats.
    if args.date_format:
        try:
            _validate_date_format(args.date_format)
        except ValueError as e:
            print(
                f"error: invalid --date-format {args.date_format!r}: {e}",
                file=sys.stderr,
            )
            return 2

    in_fh = _open_input(args.input)
    try:
        stream = _stream_with_skipped_rows(in_fh, args.skip_rows)
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if not headers:
            print("error: input has no header row", file=sys.stderr)
            return 2

        platform = args.platform or detect_platform(headers)
        if not platform:
            print(
                "error: could not detect platform from headers. "
                "Pass --platform {google,meta,tiktok,linkedin,ga4}.",
                file=sys.stderr,
            )
            return 2

        profile = PROFILES[platform]
        try:
            rows = normalize(reader, profile, args.decimal_sep, args.date_format)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    finally:
        if in_fh is not sys.stdin:
            in_fh.close()

    out_fh = _open_output(args.out)
    try:
        writer = csv.DictWriter(out_fh, fieldnames=NORMALIZED_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if out_fh is not sys.stdout:
            out_fh.close()

    print(f"normalized {len(rows)} rows ({platform})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

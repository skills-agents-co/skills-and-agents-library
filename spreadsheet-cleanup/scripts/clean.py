#!/usr/bin/env python3
"""
clean.py — deterministic cleanup for a messy finance .xlsx workbook.

Usage:
    python scripts/clean.py <input.xlsx> [--out-dir <dir>] [--detect-only]

Writes, into the output folder (default: the input file's own folder):
    <stem>.cleaned.xlsx   a cleaned copy (the input is never modified)
    <stem>.changes.json   one entry per fix/flag applied

Exit codes:
    0   cleaned successfully (report may still contain flags)
    2   refused: the input failed a safety gate, or a fatal error occurred.
        No output file is written.
    3   detect-only run (either requested with --detect-only, or the
        workbook could not be safely parsed for formulas and the script
        fell back to detect-only on its own).

This script never edits the input file. It reads the input into memory
exactly once (every gate, safety check, and parse works off that single
snapshot, never re-opening the path), and only writes a cleaned copy and a
report once everything about that snapshot has already checked out — so
there's no window where a later check can invalidate bytes something
upstream already used.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime

MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
# Applied only to members over MIN_RATIO_CHECK_BYTES compressed: a tiny,
# genuinely repetitive part (a few bytes of XML boilerplate) can innocently
# exceed a 100x ratio, so the ratio check only matters once a member is
# big enough that a high ratio is actually the sign of a bomb rather than
# noise on a small file.
MAX_COMPRESSION_RATIO = 200
MIN_RATIO_CHECK_BYTES = 4096
MAX_TOTAL_CELLS = 2_000_000
ZIP_SIGNATURE = b"PK\x03\x04"
MONTH_HEADER_RE = re.compile(r"^([A-Za-z]{3})-(\d{4})$")
MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


class Refusal(Exception):
    """Raised to abort the run with exit code 2. No output is written."""


@dataclass
class Report:
    changes: list = field(default_factory=list)
    flags: list = field(default_factory=list)

    def add_change(self, sheet, rng, before, after, rule):
        self.changes.append({
            "sheet": sheet,
            "range": rng,
            "before": before,
            "after": after,
            "rule": rule,
        })

    def add_flag(self, sheet, rng, reason, rule):
        self.flags.append({
            "sheet": sheet,
            "range": rng,
            "reason": reason,
            "rule": rule,
        })

    def to_dict(self):
        return {"changes": self.changes, "flags": self.flags}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(data):
    return hashlib.sha256(data).hexdigest()


def safe_output_path(out_dir, stem, suffix):
    """
    Build a path inside out_dir, refusing to let a crafted stem escape it,
    and refusing if a symlink already sits at that exact path. Call this
    for every path this script will actually open for writing, including
    a ".tmp" staging path — a symlink planted at the tmp name is exactly as
    dangerous as one planted at the final name, since both get opened for
    a write.
    """
    out_dir_real = os.path.realpath(out_dir)
    candidate = os.path.join(out_dir_real, stem + suffix)
    candidate_real = os.path.realpath(candidate)
    if os.path.commonpath([out_dir_real, candidate_real]) != out_dir_real:
        raise Refusal(f"refused: output path {candidate!r} would escape output dir")
    if os.path.islink(candidate):
        # realpath already resolves an existing symlink, so the check above
        # would have caught one pointing outside out_dir at the time of this
        # call — but a symlink can be planted at this exact path between this
        # check and the write that follows it. Refuse outright rather than
        # write through whatever it points at. This is still check-then-use,
        # not a closed race; it narrows the window to "between this line and
        # the write a few lines later" rather than leaving it open for the
        # whole run.
        raise Refusal(f"refused: output path {candidate!r} is a symlink")
    return candidate_real


def stem_from_input(input_path):
    base = os.path.basename(input_path)
    stem, _, _ext = base.rpartition(".")
    if not stem:
        stem = base
    # Guard against a crafted filename smuggling path separators into the stem.
    stem = re.sub(r"[\\/]+", "_", stem)
    stem = stem.replace("..", "_")
    if not stem:
        stem = "workbook"
    return stem


def read_input_snapshot(input_path):
    """
    Read the whole input file into memory exactly once. Every later check
    and the eventual openpyxl load all work off these same bytes, never
    reopening input_path — so there is no window between "validated" and
    "used" for the input's content to change underneath the run. A change
    made to the file BEFORE this read (i.e. before the size check below
    even ran) can still happen; that's caught separately, at the very end
    of clean_workbook(), by re-hashing the path itself once against a hash
    taken of this snapshot.

    The read itself is bounded to MAX_INPUT_BYTES + 1, not unbounded: an
    os.path.getsize() check followed by a separate, unbounded f.read() is
    its own TOCTOU (the file can grow between the two calls), and the
    whole point of this function is to not reintroduce that shape while
    closing a different one.
    """
    if not input_path.lower().endswith(".xlsx"):
        raise Refusal(f"refused: {input_path!r} is not a .xlsx file (by extension)")

    if not os.path.isfile(input_path):
        raise Refusal(f"refused: {input_path!r} does not exist")

    with open(input_path, "rb") as f:
        data = f.read(MAX_INPUT_BYTES + 1)

    if len(data) > MAX_INPUT_BYTES:
        raise Refusal(f"refused: {input_path!r} is over the 25MB limit")

    if data[:4] != ZIP_SIGNATURE:
        raise Refusal(f"refused: {input_path!r} does not have a zip signature (not a real .xlsx)")

    return data


def run_gate(data, input_path):
    """
    No macro parts, and a bounded total uncompressed size / compression
    ratio per member (a zip bomb can be tiny on disk and still expand to
    gigabytes; the size check in read_input_snapshot only bounds the
    compressed size on disk). Works entirely off the in-memory snapshot.
    Raises Refusal.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as e:
        raise Refusal(f"refused: {input_path!r} is not a readable zip: {e}")

    names = [zi.filename for zi in infos]

    if any(_is_macro_part(n) for n in names):
        raise Refusal(f"refused: {input_path!r} contains a macro part (macro-enabled workbook)")

    total_uncompressed = 0
    for zi in infos:
        total_uncompressed += zi.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise Refusal(
                f"refused: {input_path!r} expands to over "
                f"{MAX_UNCOMPRESSED_BYTES} bytes uncompressed (possible zip bomb)"
            )
        if (
            zi.compress_size > MIN_RATIO_CHECK_BYTES
            and zi.file_size / zi.compress_size > MAX_COMPRESSION_RATIO
        ):
            raise Refusal(
                f"refused: {input_path!r} member {zi.filename!r} has a compression "
                f"ratio over {MAX_COMPRESSION_RATIO}x (possible zip bomb)"
            )

    return names


def _is_macro_part(name):
    lname = name.lower()
    return (
        lname.endswith("vbaproject.bin")
        or lname.startswith("xl/macrosheets/")
        or lname.startswith("xl/activex/")
    )


def detect_flags(zip_names):
    """Return whether the raw zip's entries include an external-link part."""
    return any(n.startswith("xl/externalLinks/") for n in zip_names)


def validate_xml_safety(data):
    """
    Sanity-check every XML-bearing member of the workbook with defusedxml
    BEFORE any openpyxl parsing happens, so a rejected file leaves no trace
    on disk at all (there's no input copy at any point in this script —
    everything works off the in-memory snapshot passed in as `data`).
    Raises Refusal on any defusedxml-recognized attack shape.

    Covers both ".xml" parts and ".rels" relationship parts (case-
    insensitively) — openpyxl parses both as XML, and a check that only
    matched a literal lowercase ".xml" suffix left every .rels part (the
    workbook's own relationships, each sheet's relationships) unchecked.
    """
    from defusedxml import ElementTree as DET
    from defusedxml.common import DefusedXmlException

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            lname = name.lower()
            if lname.endswith(".xml") or lname.endswith(".rels"):
                member = zf.read(name)
                if not member.strip():
                    continue
                try:
                    DET.fromstring(member)
                except DefusedXmlException as e:
                    raise Refusal(f"refused: {name} contains a forbidden XML construct ({e})")
                except Exception:
                    # Not all XML-bearing members are well-formed on their
                    # own in every workbook (rare, but not our problem to
                    # diagnose); let openpyxl's own loader be the final
                    # arbiter.
                    continue


def load_workbook_safely(data):
    """Open the workbook with openpyxl from the in-memory snapshot. XML safety was already checked by validate_xml_safety()."""
    import openpyxl
    return openpyxl.load_workbook(io.BytesIO(data), data_only=False)


def col_letter(idx):
    from openpyxl.utils import get_column_letter
    return get_column_letter(idx)


def is_row_blank(ws, row_idx, max_col):
    for c in range(1, max_col + 1):
        if ws.cell(row=row_idx, column=c).value not in (None, ""):
            return False
    return True


def row_values(ws, row_idx, max_col):
    return [ws.cell(row=row_idx, column=c).value for c in range(1, max_col + 1)]


def unmerge_header(ws, report, header_row_idx):
    """
    Rule #1: unmerge a merged range that sits at or above the tabular header
    row, and keep the top-left value in place. This also covers the common
    "title row" shape (a single merged title above the real column headers,
    which find_header_row skips as a lone title row when picking
    header_row_idx) — not just a merge across the header row itself.
    Scoped this way on purpose: a merge in the body of the sheet is a
    different situation (it usually means one label spans several rows/cols
    of data on purpose), and unmerging it can make the rows below it look
    blank to the row-dropping and data-block rules that run afterward.
    """
    for merged in list(ws.merged_cells.ranges):
        if merged.min_row > header_row_idx:
            continue
        rng = str(merged)
        top_left = ws.cell(row=merged.min_row, column=merged.min_col)
        before = top_left.value
        ws.unmerge_cells(rng)
        # openpyxl restores plain cells with None value except the anchor;
        # re-assert the anchor value in case unmerge cleared it.
        ws.cell(row=merged.min_row, column=merged.min_col).value = before
        report.add_change(ws.title, rng, before, before, "unmerge_header")


def find_header_row(ws, max_col):
    """The first non-blank row is treated as the canonical header row."""
    max_row = ws.max_row
    for r in range(1, max_row + 1):
        if not is_row_blank(ws, r, max_col):
            vals = row_values(ws, r, max_col)
            # Skip a lone title row (single value spanning what used to be a
            # merged header) — a real header row has more than one label.
            non_blank = [v for v in vals if v not in (None, "")]
            if len(non_blank) >= 2:
                return r
    return None


def drop_blank_and_repeated_header_rows(ws, report):
    """
    Rule #6: delete fully-blank rows and rows that repeat the header row.
    Returns the lowest row number it deleted, or None if it deleted nothing.
    Every row at or below that number shifted up, which is what
    flag_shifted_formula_references() needs to know: openpyxl's
    delete_rows() does not rewrite formula text, so a formula that points at
    one of those rows now points at the wrong data.
    """
    max_col = ws.max_column
    header_row_idx = find_header_row(ws, max_col)
    if header_row_idx is None:
        return None
    header_vals = row_values(ws, header_row_idx, max_col)

    rows_to_delete = []
    for r in range(1, ws.max_row + 1):
        if r == header_row_idx:
            continue
        vals = row_values(ws, r, max_col)
        if all(v in (None, "") for v in vals):
            rows_to_delete.append((r, "blank_divider_row", vals))
            continue
        if vals == header_vals:
            rows_to_delete.append((r, "duplicate_header_row", vals))

    # Delete bottom-up so row indices above stay valid.
    for r, rule, vals in sorted(rows_to_delete, key=lambda t: -t[0]):
        col_last = col_letter(max_col)
        rng = f"A{r}:{col_last}{r}"
        report.add_change(ws.title, rng, vals, None, rule)
        ws.delete_rows(r, 1)

    return min((r for r, _, _ in rows_to_delete), default=None)


# Reading which rows a formula points at, without trying to understand it.
#
# A1-style reference, e.g. B5, $B$5, B$5. The lookbehind and lookahead keep it
# from matching inside a function name (LOG10, ATAN2) or a longer word, and a
# bare number like the 1.05 in =B2*1.05 has no letters in front of it so it
# never matches. The row is capped at 7 digits (Excel's last row is
# 1,048,576): a longer run of digits is not a cell reference, and capping it
# also keeps int() away from a huge run, which raises ValueError under Python
# 3.11+ and would otherwise stop the whole cleanup on one odd formula.
# \w is Unicode-aware, so a word in any script counts as a word.
CELL_REF_ROW_RE = re.compile(r"(?<!\w)\$?[A-Za-z]{1,3}\$?(\d{1,7})(?![\w(])")

# A sheet name in front of a reference: quoted ('FY 24'), or unquoted. Excel
# writes a name unquoted when it is only letters (any script), digits, "_" and
# ".", so Données!A5 and Детали!B9 arrive without quotes. An optional [n]
# in front marks a sheet in ANOTHER workbook; those are consumed and ignored.
# The name is tried only where a word starts (the lookbehind), so a long run of
# letters is scanned once and not once per character. The quoted name and the
# [n] prefix are length-capped (Excel allows 31 characters in a sheet name, 62
# with every quote doubled) so a run of quotes or brackets cannot be rescanned
# from every position.
_SHEET_PREFIX = (
    r"(?<![\w.])"
    r"(?P<ext>\[[^\[\]]{1,255}\])?"
    r"(?P<sheet>'(?:[^']|''){1,62}'|[^\W\d][\w.]*)!"
)

# Reference with a sheet name; a range's second end belongs to the same sheet.
_QUALIFIED_REF_RE = re.compile(
    _SHEET_PREFIX
    + r"\$?[A-Za-z]{1,3}\$?(?P<r1>\d{1,7})(?![\w(])"
    r"(?::\$?[A-Za-z]{1,3}\$?(?P<r2>\d{1,7})(?![\w(]))?"
)

# Whole-row references, =SUM(7:9) or =Detail!7:9, with or without a sheet name.
_ROW_RANGE_RE = re.compile(
    r"(?:" + _SHEET_PREFIX + r")?"
    r"(?<![\w.$:])\$?(?P<r1>\d{1,7}):\$?(?P<r2>\d{1,7})(?![\w(:])"
)

# Text inside double quotes, e.g. the "Q4" in ="Q4"&B2, is not a reference.
_STRING_LITERAL_RE = re.compile(r'"(?:[^"]|"")*"')

# INDIRECT and OFFSET build their target at run time, so which rows they point
# at cannot be read from the formula text.
_DYNAMIC_REF_RE = re.compile(r"(?<![\w.])(?:INDIRECT|OFFSET)\s*\(", re.IGNORECASE)

# Cap on individually listed flags per sheet, so one deletion on a big sheet
# cannot produce an unbounded report.
MAX_SHIFTED_FLAGS = 25


def formula_row_refs(formula):
    """
    Return [(sheet_name_or_None, row_number), ...] for every A1-style reference
    in the formula. None means "this formula's own sheet". A range contributes
    both of its ends. Text in double quotes is ignored.
    """
    text = _STRING_LITERAL_RE.sub('""', formula)
    refs = []

    def sheet_of(m):
        """The sheet a match points at: None for this sheet, False for another workbook."""
        if m.group("ext"):
            return False
        sheet = m.group("sheet")
        if sheet is None:
            return None
        if sheet.startswith("'"):
            sheet = sheet[1:-1].replace("''", "'")
            if sheet.startswith("["):
                return False
        return sheet

    def take_rows(m):
        sheet = sheet_of(m)
        if sheet is not False:
            refs.append((sheet, int(m.group("r1"))))
            refs.append((sheet, int(m.group("r2"))))
        return " "

    def take(m):
        sheet = sheet_of(m)
        if sheet is not False:
            refs.append((sheet, int(m.group("r1"))))
            if m.group("r2"):
                refs.append((sheet, int(m.group("r2"))))
        return " "

    if "!" in text:
        text = _QUALIFIED_REF_RE.sub(take, text)
    text = _ROW_RANGE_RE.sub(take_rows, text)
    for m in CELL_REF_ROW_RE.finditer(text):
        refs.append((None, int(m.group(1))))
    return refs


def flag_shifted_formula_references(wb, report, first_deleted_by_sheet):
    """
    Flag, without changing anything, every formula that points at a row on a
    sheet from that sheet's first deleted row down.

    openpyxl's delete_rows() moves cells but does not rewrite formula text, so
    after drop_blank_and_repeated_header_rows() removes a row, any formula
    still pointing at a row from the deleted row down now points at the wrong
    data (a total shows a neighbor's number, or zero). This is a flag only. It
    never rewrites the formula.

    `first_deleted_by_sheet` maps a sheet's title to the lowest row deleted on
    it. A reference is checked against the sheet it points at: a bare B5 is
    this formula's own sheet, and Detail!D9 is the Detail sheet. So a summary
    sheet's =Detail!D9 is flagged when Detail lost a row, and is left alone
    when it did not. Every sheet is scanned, including hidden and protected
    ones (this only reads).

    Deliberately simple: it looks only at which rows a formula references,
    never at whether two formulas have the same "shape", so it cannot mistake a
    constant like the 1.05 in =B2*1.05 for a row number. A formula is checked
    wherever it sits: a total at the top that sums a range below the deletion
    is just as stale as a formula that moved. It errs toward flagging: a
    formula that only references rows above the deletion is left alone, but
    anything at or below is listed, because the cost of a wrong extra flag is a
    person glancing at a cell, and the cost of a missed one is a wrong number
    in a finance report.

    Also flagged, because their target rows cannot be read: formulas that use
    INDIRECT or OFFSET, and array and data-table formulas (openpyxl gives those
    back as objects, not "=..." strings). For an array formula the text is
    checked like any other; a data table is flagged outright.

    It cannot see named ranges, charts, tables, conditional formatting, or
    other workbooks that link to this one, so each sheet that lost a row gets
    one note saying so.
    """
    from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

    deleted_lc = {title.lower(): row for title, row in first_deleted_by_sheet.items()}
    if not deleted_lc:
        return

    for ws in wb.worksheets:
        suspects = []  # (coordinate, reason)
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, DataTableFormula):
                    if ws.title in first_deleted_by_sheet:
                        suspects.append((
                            cell.coordinate,
                            "is a data-table formula on a sheet where a blank or repeated-header row was "
                            "deleted; its input cells may now be off. Please check it.",
                        ))
                    continue
                if isinstance(v, ArrayFormula):
                    text = v.text or ""
                elif isinstance(v, str) and v.startswith("="):
                    text = v
                else:
                    continue

                hit = None
                for sheet, ref_row in formula_row_refs(text):
                    target = ws.title if sheet is None else sheet
                    first = deleted_lc.get(target.lower())
                    if first is not None and ref_row >= first:
                        hit = (target, first)
                        break
                if hit is not None:
                    target, first = hit
                    where = "this sheet" if target == ws.title else f"sheet '{target}'"
                    suspects.append((
                        cell.coordinate,
                        f"points at or below original row {first} of {where}, where a blank or repeated-header "
                        f"row was deleted; its row references were not adjusted and may now point at the wrong "
                        f"rows. Please check it.",
                    ))
                elif _DYNAMIC_REF_RE.search(_STRING_LITERAL_RE.sub('""', text)):
                    suspects.append((
                        cell.coordinate,
                        "uses INDIRECT or OFFSET, so which rows it points at cannot be checked, and a row was "
                        "deleted in this workbook. Please check it.",
                    ))

        for coord, reason in suspects[:MAX_SHIFTED_FLAGS]:
            report.add_flag(ws.title, coord, reason, "shifted_formula_reference")
        if len(suspects) > MAX_SHIFTED_FLAGS:
            report.add_flag(
                ws.title, "<sheet>",
                f"{len(suspects) - MAX_SHIFTED_FLAGS} more formula(s) on this sheet need the same check "
                f"and are not listed individually.",
                "shifted_formula_reference",
            )
        if ws.title in first_deleted_by_sheet:
            report.add_flag(
                ws.title, "<sheet>",
                f"rows were deleted starting at original row {first_deleted_by_sheet[ws.title]}. Named "
                f"ranges, charts, tables, conditional formatting, and other workbooks that link to this "
                f"sheet were not adjusted and may be off.",
                "shifted_formula_reference",
            )


STRICT_NUMBER_RE = re.compile(
    r"^-?\$?(?:[1-9]\d{0,2}(?:,\d{3})+|0|[1-9]\d*)(\.\d+)?$",
    re.ASCII,
)


def try_parse_number(text):
    """
    Parse a currency/thousands/quote-prefixed text number. Deliberately
    strict: only a leading apostrophe, an optional '$', optional thousands
    commas grouped in 3s, and an optional decimal tail. This rejects "nan",
    "inf", "1e5", underscore-grouped floats, and anything with a leading
    zero other than a bare "0" or "0.xx" — all of which parse fine as a
    Python float but are not a finance amount (they're usually an account
    code, a ZIP code, or another identifier that must not be renumbered).
    Return (ok, number).
    """
    if not isinstance(text, str):
        return False, None
    s = text.strip()
    if s == "":
        return False, None
    stripped = s.lstrip("'")
    if not STRICT_NUMBER_RE.match(stripped):
        return False, None
    numeric = stripped.replace("$", "").replace(",", "")
    if "." in numeric:
        return True, float(numeric)
    return True, int(numeric)


def text_to_number(ws, report):
    """Rule #3: convert text-stored numbers ($, thousands commas, leading apostrophe)."""
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                ok, num = try_parse_number(cell.value)
                if ok:
                    before = cell.value
                    cell.value = num
                    report.add_change(ws.title, cell.coordinate, before, num, "text_to_number")


DIGIT_RUN_RE = re.compile(r"\d+")


def formula_shape(formula):
    """
    Generalize a formula by replacing every digit run with a placeholder, so
    two formulas that differ only in which row they reference compare equal.
    Known limitation: it strips EVERY digit run, so it cannot tell a row
    number from a numeric constant (the 1.05 in =B2*1.05). That is why it is
    only used to compare shapes for restore_column_formula's flags, and why
    stale-reference detection uses flag_shifted_formula_references() instead.
    """
    return DIGIT_RUN_RE.sub("{R}", formula)


def restore_column_formula(ws, report):
    """
    Rule #5: for each column, if every formula cell below the header row
    shares one relative shape (after generalizing away row numbers), flag
    any literal cell below the header row in that same column as a likely
    hardcoded value that should match that shape. This rule is flag-only: it never writes a formula back
    into a cell and never re-anchors an existing formula cell. If the
    column's formula cells don't share one consistent shape, flag the
    literal as suspected instead — never guess a shape from inconsistent
    formulas.

    Formulas made stale by an earlier row deletion are NOT handled here;
    flag_shifted_formula_references() does that, on its own, because it needs
    no shape comparison.
    """
    max_col = ws.max_column
    max_row = ws.max_row
    header_row_idx = find_header_row(ws, max_col) or 1

    for c in range(1, max_col + 1):
        data_rows = list(range(header_row_idx + 1, max_row + 1))
        formula_cells = []
        literal_cells = []
        for r in data_rows:
            cell = ws.cell(row=r, column=c)
            v = cell.value
            if v is None or v == "":
                continue
            if isinstance(v, str) and v.startswith("="):
                formula_cells.append((r, v))
            else:
                literal_cells.append((r, v))

        if len(formula_cells) < 2 or not literal_cells:
            continue

        shapes = {formula_shape(f) for _, f in formula_cells}
        if len(shapes) != 1:
            # No single consistent shape to restore from; don't guess.
            for r, _ in literal_cells:
                cell = ws.cell(row=r, column=c)
                report.add_flag(
                    ws.title, cell.coordinate,
                    "column has multiple formula shapes; not restored", "restore_column_formula",
                )
            continue

        # Flag the literal cell(s) that look like they should match the
        # column's shared formula shape. Never write a formula back.
        for r, _ in literal_cells:
            cell = ws.cell(row=r, column=c)
            report.add_flag(
                ws.title, cell.coordinate,
                "column's other cells share one formula shape; this literal looks like it should match — not restored",
                "restore_column_formula",
            )


def parse_month_header(text):
    if not isinstance(text, str):
        return None
    m = MONTH_HEADER_RE.match(text.strip())
    if not m:
        return None
    mon = m.group(1).lower()
    year = int(m.group(2))
    if mon not in MONTH_NAMES:
        return None
    return datetime(year, MONTH_NAMES[mon], 1)


def sheet_formulas_reference_cols(ws, cols, exclude_col):
    """
    True if any formula cell OUTSIDE `cols` (typically the "Total"-like
    column immediately after the month block) references a multi-cell RANGE
    drawn from `cols` as a block, e.g. SUM(B2:C11) — as opposed to a per-row
    SUM(Br:Cr) shape. unpivot_date_columns is flag-only and never rebuilds
    the sheet either way; this check only decides which of its two flag
    messages applies.
    """
    col_letters = {col_letter(c) for c in cols}
    range_re = re.compile(
        r"([A-Z]+)(\d+):([A-Z]+)(\d+)"
    )
    for row in ws.iter_rows():
        for cell in row:
            if cell.column == exclude_col:
                continue
            v = cell.value
            if not (isinstance(v, str) and v.startswith("=")):
                continue
            for m in range_re.finditer(v):
                c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
                if c1 in col_letters and c2 in col_letters and int(r1) != int(r2):
                    return True
    return False


def unpivot_date_columns(ws, report):
    """
    Rule #2: if 2+ header cells parse as Mon-YYYY month labels (not
    necessarily adjacent — this check only counts matching headers, it
    doesn't require them to sit next to each other), flag the sheet as
    looking like it should be unpivoted into one Date/Amount layout. This
    rule is flag-only: it never rebuilds the sheet, never clears or rewrites
    any row, and never touches the month-column headers — it only reports
    what it found. It raises exactly one flag per sheet: if another formula
    in the sheet references the month-column block as a multi-cell range the
    flag says so, otherwise it is the plain "should be one Date/Amount
    column" flag.
    """
    max_col = ws.max_column
    header_row_idx = find_header_row(ws, max_col)
    if header_row_idx is None:
        return

    month_col_idxs = []
    for c in range(1, max_col + 1):
        header_val = ws.cell(row=header_row_idx, column=c).value
        if parse_month_header(header_val) is not None:
            month_col_idxs.append(c)

    if len(month_col_idxs) < 2:
        return

    total_col = max(month_col_idxs) + 1 if max(month_col_idxs) < max_col else None
    rng = f"{col_letter(min(month_col_idxs))}{header_row_idx}:{col_letter(max(month_col_idxs))}{header_row_idx}"

    if total_col and sheet_formulas_reference_cols(ws, month_col_idxs, total_col):
        report.add_flag(
            ws.title, rng,
            "another formula references this range as a block; not unpivoted", "unpivot_date_columns",
        )
        return

    report.add_flag(
        ws.title, rng,
        "month columns look like they should be one Date/Amount column; not unpivoted",
        "unpivot_date_columns",
    )


def check_sheet_size(wb):
    """
    Refuse before any rule runs its cell-by-cell scan if a sheet's claimed
    dimensions would force an unreasonable number of cell reads. openpyxl's
    max_row/max_column reflect whatever the workbook's XML declares, which a
    crafted (or just corrupted) file can set arbitrarily high (e.g. to
    XFD1048576) with almost no bytes on disk.
    """
    for ws in wb.worksheets:
        total = (ws.max_row or 0) * (ws.max_column or 0)
        if total > MAX_TOTAL_CELLS:
            raise Refusal(
                f"refused: sheet {ws.title!r} claims {ws.max_row}x{ws.max_column} "
                f"cells ({total} total), over the {MAX_TOTAL_CELLS} cap"
            )


def detect_hidden_and_protected(ws_list):
    hidden = []
    protected = []
    for ws in ws_list:
        if ws.sheet_state != "visible":
            hidden.append(ws.title)
        if ws.protection and ws.protection.sheet:
            protected.append(ws.title)
    return hidden, protected


def clean_workbook(input_path, out_dir, detect_only_requested):
    """
    Ordering is deliberate and load-bearing, not just tidy: EVERYTHING that
    can fail — every safety gate, the workbook parse, every cleaning rule,
    and the final re-hash of input_path — runs before either final output
    path (cleaned_path / report_path) is ever touched. The two ".tmp" paths
    are the only things this function writes to until the very last two
    lines, where both get moved into place with os.replace. That means:

    - A run that fails BEFORE reaching the two os.replace calls below never
      touches cleaned_path or report_path at all, whether or not a file
      already happens to sit there from an earlier successful run. There
      is nothing to clean up on the "final" paths in that case, because
      nothing on them was ever written by THIS run — only the run's own
      ".tmp" files are removed on failure, which are always safe to remove
      because they are never anything but this run's own in-progress
      output.
    - Each of the two os.replace calls is itself atomic. Between the two
      calls is not: if the first (cleaned_path) succeeds and the second
      (report_path) then fails for some reason unrelated to this run's own
      correctness (out of disk space, a permissions change mid-run), the
      cleaned copy is this run's, but report_path is left holding an
      earlier run's report or none — a real, if narrow, inconsistent
      state this design does not fully close. Closing it completely would
      need a single cross-file transaction (a lock file, or one archive
      holding both), which isn't worth the complexity against how small
      and non-adversarial this window is once both temp files already
      exist ready to rename.

    An earlier version of this function copied the input up front and
    deleted "cleaned_path" in its failure handler whenever this run hadn't
    (yet) finished writing it — which meant a later, unrelated failure
    could delete a perfectly good file left by an EARLIER successful run.
    Never touching a final path before every check has passed removes that
    failure mode structurally instead of trying to track "did this run
    write it" as separate state.
    """
    data = read_input_snapshot(input_path)
    hash_before = sha256_of_bytes(data)

    zip_names = run_gate(data, input_path)
    validate_xml_safety(data)
    has_external_link = detect_flags(zip_names)

    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(input_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    stem = stem_from_input(input_path)
    cleaned_path = safe_output_path(out_dir, stem, ".cleaned.xlsx")
    report_path = safe_output_path(out_dir, stem, ".changes.json")
    tmp_cleaned_path = safe_output_path(out_dir, stem, ".cleaned.xlsx.tmp")
    tmp_report_path = safe_output_path(out_dir, stem, ".changes.json.tmp")

    report = Report()
    if has_external_link:
        report.add_flag("<workbook>", "xl/externalLinks/", "workbook has an external link", "external_link")

    detect_only = detect_only_requested
    will_write_cleaned_copy = False

    try:
        try:
            wb = load_workbook_safely(data)
        except Refusal:
            raise
        except Exception as e:
            eprint(f"warning: could not parse workbook for formula-aware fixes ({e}); falling back to detect-only")
            detect_only = True
            wb = None

        if wb is not None:
            check_sheet_size(wb)
            hidden, protected = detect_hidden_and_protected(wb.worksheets)
            for name in hidden:
                report.add_flag(name, "<sheet>", "hidden sheet, left unchanged", "hidden_sheet")
            for name in protected:
                report.add_flag(name, "<sheet>", "protected sheet, left unchanged", "protected_sheet")

            if not detect_only:
                first_deleted_by_sheet = {}
                for ws in wb.worksheets:
                    if ws.title in hidden or ws.title in protected:
                        continue
                    header_row_idx = find_header_row(ws, ws.max_column) or 1
                    unmerge_header(ws, report, header_row_idx)
                    first_deleted_row = drop_blank_and_repeated_header_rows(ws, report)
                    if first_deleted_row is not None:
                        first_deleted_by_sheet[ws.title] = first_deleted_row
                    text_to_number(ws, report)
                    restore_column_formula(ws, report)
                    unpivot_date_columns(ws, report)
                # After every sheet is cleaned, so a formula on one sheet is
                # checked against rows deleted on any other.
                flag_shifted_formula_references(wb, report, first_deleted_by_sheet)
                wb.save(tmp_cleaned_path)
                will_write_cleaned_copy = True

        # Re-hash the path itself (not the in-memory snapshot, which by
        # definition can't have changed) to catch a change made to the file
        # on disk between read_input_snapshot() and here. Runs BEFORE
        # either os.replace below, so a change caught here still leaves
        # both final paths untouched.
        hash_after_input = sha256_of(input_path)
        if hash_after_input != hash_before:
            raise Refusal("refused: input file changed on disk during the run")

        with open(tmp_report_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)

        if will_write_cleaned_copy:
            os.replace(tmp_cleaned_path, cleaned_path)
        os.replace(tmp_report_path, report_path)
    except BaseException:
        # Only ever the run's own in-progress temp files. cleaned_path and
        # report_path are each touched only by their own os.replace call
        # above, so an exception before those calls means neither final
        # path was touched; an exception between them (see the docstring's
        # note on that narrow window) means cleaned_path may already hold
        # this run's output while report_path does not — this handler does
        # not attempt to undo that half, since os.replace's own atomicity
        # is what's relied on, not this handler.
        for p in (tmp_cleaned_path, tmp_report_path):
            try:
                os.remove(p)
            except OSError:
                # The temp file may never have been created (e.g. the run
                # failed before reaching wb.save/open), which is the
                # expected common case, not an error to surface.
                pass
        raise

    return report, (cleaned_path if will_write_cleaned_copy else None), report_path, detect_only


def main(argv=None):
    parser = argparse.ArgumentParser(description="Clean a messy finance .xlsx workbook.")
    parser.add_argument("input", help="path to the input .xlsx file")
    parser.add_argument("--out-dir", default=None, help="output folder (default: input's own folder)")
    parser.add_argument(
        "--detect-only", action="store_true",
        help="only report hidden sheets, protected sheets, and links to other workbooks; runs none of the "
             "cleaning rules and writes no cleaned copy",
    )
    args = parser.parse_args(argv)

    try:
        report, cleaned_path, report_path, detect_only = clean_workbook(
            args.input, args.out_dir, args.detect_only
        )
    except Refusal as e:
        eprint(str(e))
        return 2
    except Exception as e:
        eprint(f"refused: unexpected error: {e}")
        return 2

    if cleaned_path is not None:
        print(f"wrote {cleaned_path}")
    print(f"wrote {report_path}")
    print(f"{len(report.changes)} change(s), {len(report.flags)} flag(s)")
    MAX_PRINTED_VALUE = 40
    def _truncated(v):
        s = repr(v)
        return s if len(s) <= MAX_PRINTED_VALUE else s[:MAX_PRINTED_VALUE] + "...(truncated)"
    for ch in report.changes:
        print(f"  fix  [{ch['rule']}] {ch['sheet']}!{ch['range']}: {_truncated(ch['before'])} -> {_truncated(ch['after'])}")
    for fl in report.flags:
        print(f"  flag [{fl['rule']}] {fl['sheet']}!{fl['range']}: {fl['reason']}")

    return 3 if detect_only else 0


if __name__ == "__main__":
    sys.exit(main())

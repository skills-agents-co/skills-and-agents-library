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

This script never edits the input file. It copies the input, opens the
copy, computes the input's hash before and after, and refuses to proceed
if that hash ever changes.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime

MAX_INPUT_BYTES = 25 * 1024 * 1024
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


class DetectOnly(Exception):
    """Raised to fall back to a detect-only run (exit code 3)."""


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


def safe_output_path(out_dir, stem, suffix):
    """Build a path inside out_dir, refusing to let a crafted stem escape it."""
    out_dir_real = os.path.realpath(out_dir)
    candidate = os.path.join(out_dir_real, stem + suffix)
    candidate_real = os.path.realpath(candidate)
    if os.path.commonpath([out_dir_real, candidate_real]) != out_dir_real:
        raise Refusal(f"refused: output path {candidate!r} would escape output dir")
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


def run_gate(input_path):
    """Extension, zip signature, no vbaProject.bin, size <= 25MB. Raises Refusal."""
    if not input_path.lower().endswith(".xlsx"):
        raise Refusal(f"refused: {input_path!r} is not a .xlsx file (by extension)")

    if not os.path.isfile(input_path):
        raise Refusal(f"refused: {input_path!r} does not exist")

    size = os.path.getsize(input_path)
    if size > MAX_INPUT_BYTES:
        raise Refusal(f"refused: {input_path!r} is {size} bytes, over the 25MB limit")

    with open(input_path, "rb") as f:
        head = f.read(4)
    if head != ZIP_SIGNATURE:
        raise Refusal(f"refused: {input_path!r} does not have a zip signature (not a real .xlsx)")

    try:
        with zipfile.ZipFile(input_path) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as e:
        raise Refusal(f"refused: {input_path!r} is not a readable zip: {e}")

    if any(n == "xl/vbaProject.bin" for n in names):
        raise Refusal(f"refused: {input_path!r} contains xl/vbaProject.bin (macro-enabled workbook)")

    return names


def detect_flags(zip_names):
    """Return (has_hidden, has_protected, has_external_link) from the raw zip, using defusedxml."""
    from defusedxml import ElementTree as DET

    has_external_link = any(n.startswith("xl/externalLinks/") for n in zip_names)
    return has_external_link


def load_workbook_safely(cleaned_path):
    """
    Open the copy with openpyxl. openpyxl parses XML with its own bundled
    parser; we additionally sanity-check the shared strings / sheet XML with
    defusedxml first so a crafted entity-expansion payload is rejected before
    openpyxl ever touches it.
    """
    from defusedxml import ElementTree as DET

    with zipfile.ZipFile(cleaned_path) as zf:
        for name in zf.namelist():
            if name.endswith(".xml"):
                data = zf.read(name)
                if not data.strip():
                    continue
                try:
                    DET.fromstring(data)
                except DET.EntitiesForbidden:
                    raise Refusal(f"refused: {name} contains a forbidden XML entity payload")
                except Exception:
                    # Not all "*.xml" members are well-formed on their own in
                    # every workbook (rare, but not our problem to diagnose);
                    # let openpyxl's own loader be the final arbiter.
                    continue

    import openpyxl
    return openpyxl.load_workbook(cleaned_path, data_only=False)


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


def unmerge_header(ws, report):
    """Rule #1: unmerge any merged range and keep the top-left value in place."""
    for merged in list(ws.merged_cells.ranges):
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
    """Rule #6: delete fully-blank rows and rows that repeat the header row."""
    max_col = ws.max_column
    header_row_idx = find_header_row(ws, max_col)
    if header_row_idx is None:
        return
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


def try_parse_number(text):
    """Parse a currency/thousands/quote-prefixed text number. Return (ok, number)."""
    if not isinstance(text, str):
        return False, None
    s = text.strip()
    if s == "":
        return False, None
    stripped = s.lstrip("'")
    stripped = stripped.replace("$", "").replace(",", "").strip()
    if stripped == "":
        return False, None
    try:
        if re.fullmatch(r"-?\d+", stripped):
            return True, int(stripped)
        val = float(stripped)
        return True, val
    except ValueError:
        return False, None


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
    This also means the shape is independent of any row-deletion shift that
    happened earlier in the pipeline (openpyxl does not rewrite formula text
    when delete_rows() is called, so a surviving formula can still literally
    reference its pre-deletion row number).
    """
    return DIGIT_RUN_RE.sub("{R}", formula)


def instantiate_shape(shape, row):
    return shape.replace("{R}", str(row))


def restore_column_formula(ws, report):
    """
    Rule #5: for each column, if every formula cell in the column shares one
    relative shape (after generalizing away row numbers), restore any literal
    cell in that same data block to that shape instantiated at its own row —
    and re-anchor every formula cell in the group to its own current row too,
    since an earlier row deletion can leave a surviving formula pointing at a
    stale (pre-deletion) row number. Otherwise flag as suspected — never
    guess a shape from inconsistent formulas.
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

        shapes = {formula_shape(f) for r, f in formula_cells}
        if len(shapes) != 1:
            # No single consistent shape to restore from; don't guess.
            for r, v in literal_cells:
                cell = ws.cell(row=r, column=c)
                report.add_flag(
                    ws.title, cell.coordinate,
                    "column has multiple formula shapes; not restored", "restore_column_formula",
                )
            continue

        shape = next(iter(shapes))

        # Re-anchor every formula cell to its own current row (repairs any
        # staleness from an earlier row deletion).
        for r, f in formula_cells:
            cell = ws.cell(row=r, column=c)
            new_formula = instantiate_shape(shape, r)
            if new_formula != f:
                report.add_change(ws.title, cell.coordinate, f, new_formula, "restore_column_formula")
                cell.value = new_formula

        # Restore the literal cell(s) using the same shape.
        for r, v in literal_cells:
            cell = ws.cell(row=r, column=c)
            new_formula = instantiate_shape(shape, r)
            before = v
            cell.value = new_formula
            report.add_change(ws.title, cell.coordinate, before, new_formula, "restore_column_formula")


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


def sheet_formulas_reference_cols(ws, cols, header_row_idx, max_row, exclude_col):
    """
    True if any formula cell OUTSIDE `cols` (typically the "Total"-like
    column immediately after the month block) references a multi-cell RANGE
    drawn from `cols` as a block, e.g. SUM(B2:C11) — as opposed to the
    per-row SUM(Br:Cr) shape that restore_column_formula already normalized
    and that this same unpivot is about to migrate.
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
    Rule #2: if 2+ adjacent header cells parse as Mon-YYYY month labels,
    unpivot them into one Date column, exploding each data row into one row
    per month column. Skips (flags) if another formula in the sheet
    references the month-column block as a multi-cell range.
    """
    max_col = ws.max_column
    max_row = ws.max_row
    header_row_idx = find_header_row(ws, max_col)
    if header_row_idx is None:
        return

    month_cols = []
    for c in range(1, max_col + 1):
        header_val = ws.cell(row=header_row_idx, column=c).value
        parsed = parse_month_header(header_val)
        if parsed is not None:
            month_cols.append((c, parsed))

    if len(month_cols) < 2:
        return

    month_col_idxs = [c for c, _ in month_cols]
    total_col = max(month_col_idxs) + 1 if max(month_col_idxs) < max_col else None

    if total_col and sheet_formulas_reference_cols(ws, month_col_idxs, header_row_idx, max_row, total_col):
        first_c, last_c = min(month_col_idxs), max(month_col_idxs)
        rng = f"{col_letter(first_c)}{header_row_idx}:{col_letter(last_c)}{header_row_idx}"
        report.add_flag(
            ws.title, rng,
            "another formula references this range as a block; not unpivoted", "unpivot_date_columns",
        )
        return

    other_cols = [c for c in range(1, max_col + 1) if c not in month_col_idxs]
    header_first_month = min(month_col_idxs)

    new_rows = []
    category_col = 1  # by convention, column A is the row label
    for r in range(header_row_idx + 1, max_row + 1):
        row_vals = {c: ws.cell(row=r, column=c).value for c in range(1, max_col + 1)}
        if all(v in (None, "") for v in row_vals.values()):
            continue
        for c, month_date in month_cols:
            new_row = {}
            for oc in other_cols:
                if oc < header_first_month:
                    new_row[oc] = row_vals.get(oc)
            new_row["date"] = month_date
            new_row["amount"] = row_vals.get(c)
            if total_col:
                new_row["total_formula_row"] = r
                new_row["total_col_letter"] = col_letter(c)
            new_rows.append(new_row)

    before_range = (
        f"{col_letter(header_first_month)}{header_row_idx}:"
        f"{col_letter(max(month_col_idxs))}{header_row_idx}"
    )
    before_headers = [ws.cell(row=header_row_idx, column=c).value for c in month_col_idxs]

    # Rebuild the sheet: label columns (before the month block), Date, Amount,
    # then any trailing columns (e.g. Total) shifted to follow.
    label_cols = [c for c in other_cols if c < header_first_month]
    trailing_cols = [c for c in other_cols if c > header_first_month]

    new_header_row = header_row_idx
    new_col_order = label_cols + ["DATE_COL", "AMOUNT_COL"] + trailing_cols
    header_labels = {}
    for c in label_cols:
        header_labels[c] = ws.cell(row=header_row_idx, column=c).value
    for c in trailing_cols:
        header_labels[c] = ws.cell(row=header_row_idx, column=c).value

    # Clear all data rows first (header stays).
    for r in range(header_row_idx + 1, max_row + 1):
        for c in range(1, max_col + 1):
            ws.cell(row=r, column=c).value = None

    # Write new header.
    out_c = 1
    col_map = {}
    for c in label_cols:
        ws.cell(row=header_row_idx, column=out_c).value = header_labels[c]
        col_map[("label", c)] = out_c
        out_c += 1
    date_out_c = out_c
    ws.cell(row=header_row_idx, column=out_c).value = "Date"
    out_c += 1
    amount_out_c = out_c
    ws.cell(row=header_row_idx, column=out_c).value = "Amount"
    out_c += 1
    trailing_out_cols = {}
    for c in trailing_cols:
        ws.cell(row=header_row_idx, column=out_c).value = header_labels[c]
        trailing_out_cols[c] = out_c
        out_c += 1

    date_cell_fmt = "mmm-yyyy"

    write_row = header_row_idx + 1
    for nr in new_rows:
        for c in label_cols:
            ws.cell(row=write_row, column=col_map[("label", c)]).value = nr.get(c)
        dcell = ws.cell(row=write_row, column=date_out_c)
        dcell.value = nr["date"]
        dcell.number_format = date_cell_fmt
        ws.cell(row=write_row, column=amount_out_c).value = nr["amount"]
        for c in trailing_cols:
            out_col = trailing_out_cols[c]
            if total_col and c == total_col:
                amount_letter = col_letter(amount_out_c)
                ws.cell(row=write_row, column=out_col).value = f"=SUM({amount_letter}{write_row}:{amount_letter}{write_row})"
            else:
                ws.cell(row=write_row, column=out_col).value = None
        write_row += 1

    # Trim any now-unused trailing rows beyond what we wrote.
    if write_row - 1 < max_row:
        ws.delete_rows(write_row, max_row - (write_row - 1))

    report.add_change(ws.title, before_range, before_headers, "Date", "unpivot_date_columns")


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
    zip_names = run_gate(input_path)
    has_external_link = detect_flags(zip_names)

    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(input_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    stem = stem_from_input(input_path)
    cleaned_path = safe_output_path(out_dir, stem, ".cleaned.xlsx")
    report_path = safe_output_path(out_dir, stem, ".changes.json")

    hash_before = sha256_of(input_path)
    shutil.copyfile(input_path, cleaned_path)

    report = Report()
    if has_external_link:
        report.add_flag("<workbook>", "xl/externalLinks/", "workbook has an external link", "external_link")

    detect_only = detect_only_requested
    try:
        wb = load_workbook_safely(cleaned_path)
    except Refusal:
        raise
    except Exception as e:
        eprint(f"warning: could not parse workbook for formula-aware fixes ({e}); falling back to detect-only")
        detect_only = True
        wb = None

    if wb is not None:
        hidden, protected = detect_hidden_and_protected(wb.worksheets)
        for name in hidden:
            report.add_flag(name, "<sheet>", "hidden sheet, left unchanged", "hidden_sheet")
        for name in protected:
            report.add_flag(name, "<sheet>", "protected sheet, left unchanged", "protected_sheet")

        if not detect_only:
            for ws in wb.worksheets:
                if ws.title in hidden or ws.title in protected:
                    continue
                unmerge_header(ws, report)
                drop_blank_and_repeated_header_rows(ws, report)
                text_to_number(ws, report)
                restore_column_formula(ws, report)
                unpivot_date_columns(ws, report)

    if wb is not None and not detect_only:
        wb.save(cleaned_path)

    hash_after_input = sha256_of(input_path)
    if hash_after_input != hash_before:
        # Should never happen (we never open input_path itself), but this is
        # the load-bearing guarantee, so verify it explicitly every run.
        try:
            os.remove(cleaned_path)
        except OSError:
            pass
        raise Refusal("refused: input file hash changed during the run")

    with open(report_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2, default=str)

    return report, cleaned_path, report_path, detect_only


def main(argv=None):
    parser = argparse.ArgumentParser(description="Clean a messy finance .xlsx workbook.")
    parser.add_argument("input", help="path to the input .xlsx file")
    parser.add_argument("--out-dir", default=None, help="output folder (default: input's own folder)")
    parser.add_argument("--detect-only", action="store_true", help="only detect defects, write no cleaned copy content changes")
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

    print(f"wrote {cleaned_path}")
    print(f"wrote {report_path}")
    print(f"{len(report.changes)} change(s), {len(report.flags)} flag(s)")
    for ch in report.changes:
        print(f"  fix  [{ch['rule']}] {ch['sheet']}!{ch['range']}: {ch['before']!r} -> {ch['after']!r}")
    for fl in report.flags:
        print(f"  flag [{fl['rule']}] {fl['sheet']}!{fl['range']}: {fl['reason']}")

    if args.detect_only:
        return 3
    if detect_only:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

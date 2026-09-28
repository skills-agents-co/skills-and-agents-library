#!/usr/bin/env python3
"""
run_evals.py — golden-case release gate for the spreadsheet-cleanup skill.

Drives success criteria 1-7 from CONTRIBUTING.md / the skill's Eval Contract,
against the frozen fixtures in evals/spreadsheet-cleanup/fixtures/ (copied
from skills-and-agents-marketplace @ 6572bf5) plus guard-case workbooks this
script builds itself in a temp folder at run time.

Usage:  python evals/spreadsheet-cleanup/run_evals.py
Exit:   0 if every case passes, 1 otherwise.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
FIXTURES = os.path.join(HERE, "fixtures")
CLEAN_PY = os.path.join(REPO_ROOT, "spreadsheet-cleanup", "scripts", "clean.py")

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_clean(input_path, out_dir, extra_args=None):
    args = [sys.executable, CLEAN_PY, input_path, "--out-dir", out_dir]
    if extra_args:
        args += extra_args
    res = subprocess.run(args, capture_output=True, text=True)
    return res


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def load_report(out_dir, input_path):
    report_path = os.path.join(out_dir, stem(input_path) + ".changes.json")
    if not os.path.isfile(report_path):
        return None
    with open(report_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Criteria 1, 2, 3: messy.xlsx fixes every manifest defect, report is complete,
# input hash is unchanged.
# ---------------------------------------------------------------------------

def eval_messy(tmp):
    import openpyxl

    messy_src = os.path.join(FIXTURES, "messy.xlsx")
    manifest_path = os.path.join(FIXTURES, "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    out_dir = os.path.join(tmp, "messy_out")
    os.makedirs(out_dir, exist_ok=True)

    hash_before = sha256_of(messy_src)
    res = run_clean(messy_src, out_dir)
    hash_after = sha256_of(messy_src)

    check("messy.xlsx: clean.py exits 0", res.returncode == 0, res.stderr)
    check("messy.xlsx: input file hash unchanged", hash_before == hash_after)

    cleaned_path = os.path.join(out_dir, "messy.cleaned.xlsx")
    check("messy.xlsx: cleaned copy was written", os.path.isfile(cleaned_path))
    if not os.path.isfile(cleaned_path):
        return

    report = load_report(out_dir, messy_src)
    check("messy.xlsx: change report was written", report is not None)
    if report is None:
        return

    changes = report.get("changes", [])
    for entry in changes:
        for key in ("sheet", "range", "before", "after", "rule"):
            check(f"messy.xlsx: change entry has '{key}'", key in entry, json.dumps(entry))

    wb = openpyxl.load_workbook(cleaned_path, data_only=False)
    ws = wb["Expenses"]
    wb_in = openpyxl.load_workbook(messy_src, data_only=False)
    ws_in = wb_in["Expenses"]

    # Defect 1: merged header gone.
    check("messy.xlsx: A1:D1 no longer merged", "A1:D1" not in {str(r) for r in ws.merged_cells.ranges})

    # Defect 2 (flag-only): month columns are left exactly as they were — not
    # unpivoted, not restructured. This rule only ever flags now.
    header_row = None
    for r in range(1, ws.max_row + 1):
        vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        if any(v == "Category" for v in vals):
            header_row = r
            break
    check("messy.xlsx: header row found", header_row is not None)
    header_vals = []
    if header_row:
        header_vals = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]
    check(
        "messy.xlsx: month columns Jan-2026/Feb-2026 are still separate header columns (not unpivoted)",
        header_row is not None and "Jan-2026" in header_vals and "Feb-2026" in header_vals and "Date" not in header_vals,
        str(header_vals),
    )

    # Deleting the blank divider row and the duplicate header row (defect 6)
    # shifts every row below them up by two IN THE CLEANED COPY ONLY — the
    # input keeps its original row numbers, since it's never modified. So
    # defects 3 and 5 are checked by category label (column A), never by a
    # fixed coordinate, to compare the same logical row on both sides
    # regardless of that shift — and every lookup here uses
    # ws.cell(row=, column=), never ws["<coord>"], since indexing openpyxl by
    # a string coordinate past the sheet's current bounds silently grows
    # max_row/max_column with a blank cell, which would corrupt the defect-6
    # blank-row check below.
    CATEGORY_LABELS = ("Rent", "Utilities", "Payroll", "Marketing", "Travel", "Software", "Insurance")

    def row_by_category(sheet, label, max_r):
        for r in range(1, max_r + 1):
            if sheet.cell(row=r, column=1).value == label:
                return r
        return None

    cleaned_rows_by_cat = {label: row_by_category(ws, label, ws.max_row) for label in CATEGORY_LABELS}
    input_rows_by_cat = {label: row_by_category(ws_in, label, ws_in.max_row) for label in CATEGORY_LABELS}
    for label in CATEGORY_LABELS:
        check(f"messy.xlsx: category '{label}' found in cleaned copy", cleaned_rows_by_cat[label] is not None)
        check(f"messy.xlsx: category '{label}' found in input", input_rows_by_cat[label] is not None)
    if None in cleaned_rows_by_cat.values() or None in input_rows_by_cat.values():
        return

    # Defect 3: text-stored numbers converted to real numbers with the right values.
    text_to_num_expected = {"Travel": 1000, "Software": 1200, "Insurance": 2200}
    text_to_num_actual = {
        label: ws.cell(row=cleaned_rows_by_cat[label], column=2).value
        for label in text_to_num_expected
    }
    check(
        "messy.xlsx: former text amounts (Travel/Software/Insurance, col B) are now numeric 1000/1200/2200",
        text_to_num_actual == text_to_num_expected,
        str(text_to_num_actual),
    )

    # Defect 5 (flag-only): Marketing's hardcoded D-column literal is left
    # completely untouched (still 3100, not a restored formula), and every
    # other formula cell in the column is byte-identical to the input's own
    # cell for that same category — no re-anchoring, no rewrite of any kind.
    marketing_cleaned_d = ws.cell(row=cleaned_rows_by_cat["Marketing"], column=4).value
    marketing_input_d = ws_in.cell(row=input_rows_by_cat["Marketing"], column=4).value
    check(
        "messy.xlsx: Marketing's D-column hardcoded literal is untouched (still 3100)",
        marketing_cleaned_d == marketing_input_d == 3100,
        f"cleaned={marketing_cleaned_d!r} input={marketing_input_d!r}",
    )
    for label in ("Rent", "Utilities", "Payroll", "Travel", "Software", "Insurance"):
        cleaned_d = ws.cell(row=cleaned_rows_by_cat[label], column=4).value
        input_d = ws_in.cell(row=input_rows_by_cat[label], column=4).value
        check(
            f"messy.xlsx: {label}'s D-column formula is byte-identical to input (not re-anchored)",
            cleaned_d == input_d,
            f"cleaned={cleaned_d!r} input={input_d!r}",
        )

    # Rows below the blank-divider/duplicate-header deletion (Travel, Software,
    # Insurance) shift up by two, so their surviving D-column formulas still
    # literally reference their pre-deletion row numbers (=SUM(B9:C9) etc.
    # sitting at row 7). Nothing rewrites them (checked above), so the run
    # must at least SAY so: each gets a "shifted_formula_reference" flag.
    # Rent, Utilities, and Payroll reference rows 3-5, above the first
    # deleted row (7), so they were never affected and must not be flagged.
    # The exact set is pinned, so a spurious extra flag anywhere also fails.
    flags_all = report.get("flags", [])
    shifted_cells = {
        f["range"] for f in flags_all
        if f["rule"] == "shifted_formula_reference" and f["range"] != "<sheet>"
    }
    expected_shifted = {
        ws.cell(row=cleaned_rows_by_cat[label], column=4).coordinate
        for label in ("Travel", "Software", "Insurance")
    }
    check(
        "messy.xlsx: exactly Travel/Software/Insurance's D-column formulas are flagged as shifted",
        shifted_cells == expected_shifted,
        f"flagged={sorted(shifted_cells)} expected={sorted(expected_shifted)}",
    )
    check(
        "messy.xlsx: a sheet-level note says where deletion started and that named ranges, charts, etc. were not adjusted",
        any(
            f["rule"] == "shifted_formula_reference" and f["range"] == "<sheet>"
            and "starting at original row 7" in f["reason"] and "Named ranges" in f["reason"]
            for f in flags_all
        ),
        json.dumps([f for f in flags_all if f["rule"] == "shifted_formula_reference"]),
    )

    # Defect 2 continued: unpivot_date_columns is flag-only, so the month
    # DATA cells (columns B and C), not just the header row, must be
    # byte-identical to the input for every category — a regression that
    # rewrote or cleared data rows while leaving the header alone would
    # otherwise pass unnoticed.
    for label in ("Rent", "Utilities", "Payroll", "Marketing"):
        for col, col_name in ((2, "B"), (3, "C")):
            cleaned_v = ws.cell(row=cleaned_rows_by_cat[label], column=col).value
            input_v = ws_in.cell(row=input_rows_by_cat[label], column=col).value
            check(
                f"messy.xlsx: {label}'s column {col_name} (month data) is byte-identical to input (not unpivoted)",
                cleaned_v == input_v,
                f"cleaned={cleaned_v!r} input={input_v!r}",
            )
    # Travel/Software/Insurance's column B is converted by text_to_number on
    # purpose (checked above); column C for those three is untouched by any
    # rule and must still match the input exactly.
    for label in ("Travel", "Software", "Insurance"):
        cleaned_c = ws.cell(row=cleaned_rows_by_cat[label], column=3).value
        input_c = ws_in.cell(row=input_rows_by_cat[label], column=3).value
        check(
            f"messy.xlsx: {label}'s column C (month data) is byte-identical to input (not unpivoted)",
            cleaned_c == input_c,
            f"cleaned={cleaned_c!r} input={input_c!r}",
        )

    # Defect 6: blank divider row and duplicate header row are gone.
    all_rows = []
    for r in range(1, ws.max_row + 1):
        all_rows.append([ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)])
    blank_rows = [row for row in all_rows if all(v in (None, "") for v in row)]
    header_like_rows = [row for row in all_rows if row == header_vals]
    check("messy.xlsx: no fully-blank divider row remains", len(blank_rows) == 0, str(all_rows))
    check("messy.xlsx: no repeated header row remains", len(header_like_rows) <= 1, str(all_rows))

    # Every manifest defect maps to at least one report entry. wide_date_columns
    # and hardcoded_formula_value are flag-only now, so those two are checked
    # against report["flags"] instead of report["changes"].
    defect_ids = [d["id"] for d in manifest["messy"]["defects"]]
    rules_seen = {c["rule"] for c in changes}
    flags = report.get("flags", [])
    flag_rules_seen = {f["rule"] for f in flags}
    flag_only_defects = {"wide_date_columns", "hardcoded_formula_value"}
    defect_to_rule = {
        "merged_header": "unmerge_header",
        "wide_date_columns": "unpivot_date_columns",
        "numbers_as_text_currency": "text_to_number",
        "numbers_as_text_comma": "text_to_number",
        "numbers_as_text_apostrophe": "text_to_number",
        "hardcoded_formula_value": "restore_column_formula",
        "blank_divider_row": "blank_divider_row",
        "duplicate_header_row": "duplicate_header_row",
    }
    for defect_id in defect_ids:
        expected_rule = defect_to_rule[defect_id]
        if defect_id in flag_only_defects:
            check(
                f"messy.xlsx: manifest defect '{defect_id}' has a matching flag entry",
                expected_rule in flag_rules_seen,
                f"flag rules seen: {flag_rules_seen}",
            )
        else:
            check(
                f"messy.xlsx: manifest defect '{defect_id}' has a matching report entry",
                expected_rule in rules_seen,
                f"rules seen: {rules_seen}",
            )

    # Neither flag-only rule may EVER produce a "changes" entry, written cell
    # or not — that's the whole point of making them flag-only. A regression
    # that logged a change (with or without an actual write) for either rule
    # would otherwise slip through every check above.
    check(
        "messy.xlsx: restore_column_formula and unpivot_date_columns never appear in report['changes']",
        rules_seen.isdisjoint({"restore_column_formula", "unpivot_date_columns"}),
        f"rules seen in changes: {rules_seen}",
    )


def run_fixture(tmp, name, sheets, extra_args=None):
    """
    Build a workbook from {sheet_title: [rows]} (dict order is sheet order),
    run clean.py on it, and return (report, cleaned_path). Always records the
    exit-code and report-written checks, so a case can never pass by silently
    skipping its assertions because the run failed. `report` is None if none
    was written.
    """
    import openpyxl

    path = os.path.join(tmp, name + ".xlsx")
    wb = openpyxl.Workbook()
    for i, (title, rows) in enumerate(sheets.items()):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = title
        for row in rows:
            ws.append(row)
    wb.save(path)
    out = os.path.join(tmp, name + "_out")
    os.makedirs(out, exist_ok=True)
    res = run_clean(path, out, extra_args)
    want = 3 if extra_args and "--detect-only" in extra_args else 0
    check(f"{name}: clean.py exits {want}", res.returncode == want, res.stderr)
    report = load_report(out, path)
    check(f"{name}: report was written", report is not None)
    return report, os.path.join(out, name + ".cleaned.xlsx")


SHIFTED = "shifted_formula_reference"


def shifted_cells(report, sheet=None):
    """Coordinates flagged by the shifted-formula rule (not the per-sheet notes)."""
    return {
        f["range"] for f in report.get("flags", [])
        if f["rule"] == SHIFTED and f["range"] != "<sheet>" and (sheet is None or f["sheet"] == sheet)
    }


def shifted_notes(report, sheet):
    """The per-sheet '<sheet>' flags for the shifted-formula rule."""
    return [
        f for f in report.get("flags", [])
        if f["rule"] == SHIFTED and f["range"] == "<sheet>" and f["sheet"] == sheet
    ]


def eval_flag_only_edge_cases(tmp):
    """
    The flag-only rules and the shifted-formula flag, driven by small purpose-
    built workbooks: restore_column_formula's mixed-shapes path,
    unpivot_date_columns' block-reference path and non-adjacent months, and
    flag_shifted_formula_references (boundary, separated deletions, totals row,
    constants, string literals, function names, other sheets, array formulas,
    INDIRECT/OFFSET, the 25-flag cap, --detect-only, and a huge digit run).
    """
    import openpyxl

    # A: a column of formulas with no single consistent shape, plus a literal.
    # Must be flagged as "multiple formula shapes" on the literal (D4), and the
    # literal must be left completely untouched.
    report, cleaned = run_fixture(tmp, "mixed_shapes", {"Sheet": [
        ["Category", "B", "C", "Total"],
        ["Rent", 100, 5, "=B2+C2"],
        ["Utilities", 200, 3, "=B3*C3"],   # different shape on purpose
        ["Payroll", 300, 2, 999],          # the literal that must stay untouched
    ]})
    if report is not None:
        flags = report.get("flags", [])
        check(
            "mixed formula shapes: flagged as 'column has multiple formula shapes' on D4",
            any(
                f["rule"] == "restore_column_formula"
                and "multiple formula shapes" in f["reason"]
                and f["range"] == "D4"
                for f in flags
            ),
            json.dumps(flags),
        )
        check(
            "mixed formula shapes: no change entries for restore_column_formula",
            not any(c["rule"] == "restore_column_formula" for c in report.get("changes", [])),
            json.dumps(report.get("changes", [])),
        )
        d4 = openpyxl.load_workbook(cleaned, data_only=False)["Sheet"].cell(row=4, column=4).value
        check("mixed formula shapes: the literal cell is untouched (still 999)", d4 == 999, repr(d4))

    # B: month columns where another formula references the month block as a
    # range. total_col only exists (so the block-reference guard only runs)
    # when the month block doesn't reach the sheet's last column, hence the
    # trailing "Total"; the referencing formula sits in column A, outside the
    # excluded Total column. Must flag "references this range as a block" and
    # leave the header AND every data cell exactly as given.
    rows_b = [
        ["Category", "Jan-2026", "Feb-2026", "Total"],
        ["Rent", 100, 200, "=B2+C2"],
        ["Utilities", 150, 250, "=B3+C3"],
        ["=SUM(B2:C3)", None, None, None],
    ]
    report, cleaned = run_fixture(tmp, "block_ref", {"Sheet": rows_b})
    if report is not None:
        flags_b = report.get("flags", [])
        check(
            "block-referenced months: flagged as 'references this range as a block'",
            any(f["rule"] == "unpivot_date_columns" and "references this range as a block" in f["reason"] for f in flags_b),
            json.dumps(flags_b),
        )
        check(
            "block-referenced months: exactly one unpivot flag (the plain one is not also raised)",
            sum(1 for f in flags_b if f["rule"] == "unpivot_date_columns") == 1,
            json.dumps(flags_b),
        )
        check(
            "block-referenced months: no change entries for unpivot_date_columns",
            not any(c["rule"] == "unpivot_date_columns" for c in report.get("changes", [])),
            json.dumps(report.get("changes", [])),
        )
        ws_b = openpyxl.load_workbook(cleaned, data_only=False)["Sheet"]
        got_b = [[ws_b.cell(row=r, column=c).value for c in range(1, 5)] for r in range(1, 5)]
        want_b = [[v for v in row] for row in rows_b]
        check(
            "block-referenced months: every cell (header and data) is unchanged",
            got_b == want_b,
            f"got={got_b} want={want_b}",
        )

    # Q: month columns that are NOT next to each other. One flag whose range
    # spans the gap; the column in between and all data are untouched.
    report, cleaned = run_fixture(tmp, "months_apart", {"Sheet": [
        ["Item", "Jan-2026", "Notes", "Feb-2026"],
        ["a", 1, "keep me", 2],
    ]})
    if report is not None:
        uf = [f for f in report.get("flags", []) if f["rule"] == "unpivot_date_columns"]
        check("non-adjacent months: one unpivot flag spanning B1:D1", len(uf) == 1 and uf[0]["range"] == "B1:D1", json.dumps(uf))
        ws_q = openpyxl.load_workbook(cleaned, data_only=False)["Sheet"]
        check(
            "non-adjacent months: the column between them is untouched",
            [ws_q.cell(row=r, column=3).value for r in (1, 2)] == ["Notes", "keep me"],
        )

    # C: an ALL-formula column (no literal at all) below a deleted
    # blank/duplicate-header pair. D2 sits above the deletion and never moves.
    report, cleaned = run_fixture(tmp, "all_formula_stale", {"Sheet": [
        ["Category", "B", "C", "Total"],     # row 1: header
        ["A", 10, 1, "=B2+C2"],              # row 2: above the deletion
        [None, None, None, None],            # row 3: blank divider (deleted)
        ["Category", "B", "C", "Total"],     # row 4: duplicate header (deleted)
        ["Bee", 20, 2, "=B5+C5"],            # row 5 -> row 3, stale
        ["Cee", 30, 3, "=B6+C6"],            # row 6 -> row 4, stale
    ]})
    if report is not None:
        check("all-formula stale column: exactly D3 and D4 are flagged", shifted_cells(report) == {"D3", "D4"}, str(sorted(shifted_cells(report))))
        check(
            "all-formula stale column: no change entries for the shifted-formula rule",
            not any(c["rule"] == SHIFTED for c in report.get("changes", [])),
        )
        ws_c = openpyxl.load_workbook(cleaned, data_only=False)["Sheet"]
        check(
            "all-formula stale column: shifted formulas keep their text",
            [ws_c.cell(row=r, column=4).value for r in (2, 3, 4)] == ["=B2+C2", "=B5+C5", "=B6+C6"],
        )

    # D: a correct column with a constant multiplier and NO deleted row: nothing
    # can be stale, so no flags and no changes.
    report, _ = run_fixture(tmp, "clean_multiplier", {"Sheet": [
        ["Category", "Amount", "WithTax"],
        ["Rent", 100, "=B2*1.05"],
        ["Food", 200, "=B3*1.05"],
        ["Gas", 300, "=B4*1.05"],
    ]})
    if report is not None:
        check("clean multiplier column: no flags at all", report.get("flags", []) == [], json.dumps(report.get("flags", [])))
        check("clean multiplier column: no changes at all", report.get("changes", []) == [], json.dumps(report.get("changes", [])))

    # E: per-row formulas PLUS a totals row (two formula shapes in one column),
    # with a blank divider in the middle. The totals row must be flagged too.
    report, _ = run_fixture(tmp, "totals_row", {"Sheet": [
        ["Item", "Qty", "Price", "Line"],
        ["a", 1, 2, "=B2*C2"],
        ["b", 1, 2, "=B3*C3"],
        ["c", 1, 2, "=B4*C4"],
        [None, None, None, None],            # row 5: blank divider (deleted)
        ["d", 1, 2, "=B6*C6"],
        ["e", 1, 2, "=B7*C7"],
        ["f", 1, 2, "=B8*C8"],
        ["Total", None, None, "=SUM(D2:D8)"],
    ]})
    if report is not None:
        check(
            "totals row: shifted rows AND the totals formula are flagged, rows above the deletion are not",
            shifted_cells(report) == {"D5", "D6", "D7", "D8"},
            str(sorted(shifted_cells(report))),
        )

    # F: a numeric constant with a deletion. =B4*1.05 references row 4, at or
    # below the deleted row 3, so it is flagged; =B2*1.05 above it is not.
    report, _ = run_fixture(tmp, "constant_with_deletion", {"Sheet": [
        ["Category", "Amount", "WithTax"],
        ["Rent", 100, "=B2*1.05"],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["Food", 200, "=B4*1.05"],
        ["Gas", 300, "=B5*1.05"],
    ]})
    if report is not None:
        check(
            "constant with deletion: only the two shifted formulas are flagged",
            shifted_cells(report) == {"C3", "C4"},
            str(sorted(shifted_cells(report))),
        )

    # G: a lone total ABOVE the deletion summing a range below it. It did not
    # move and is the only formula in its column, but its range is now wrong.
    report, cleaned = run_fixture(tmp, "lone_total_above", {"Sheet": [
        ["Category", "Amount"],
        ["Total", "=SUM(B4:B6)"],
        [None, None],                        # row 3: blank divider (deleted)
        ["A", 10], ["B", 20], ["C", 30],
    ]})
    if report is not None:
        check("lone total above the deletion: flagged though it did not move", shifted_cells(report) == {"B2"}, str(sorted(shifted_cells(report))))
        got = openpyxl.load_workbook(cleaned, data_only=False)["Sheet"].cell(row=2, column=2).value
        check("lone total above the deletion: formula text unchanged", got == "=SUM(B4:B6)", repr(got))

    # I: the boundary. Row 3 is the deleted row. =B3 references exactly that
    # row, so it is flagged; =B2 references the row just above, so it is not.
    report, _ = run_fixture(tmp, "boundary", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, "=B2"],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, "=B3"],
    ]})
    if report is not None:
        check(
            "boundary: a reference to exactly the deleted row is flagged, the row above is not",
            shifted_cells(report) == {"C3"},
            str(sorted(shifted_cells(report))),
        )

    # J: two SEPARATED deletions (rows 3 and 7). The formula on original row 5
    # references row 5, which sits between them and did move. The flag must
    # start at the LOWEST deleted row, so it is flagged; starting at the
    # highest would miss it.
    report, _ = run_fixture(tmp, "separated_deletions", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, None],
        [None, None, None],                  # row 3: blank (deleted)
        ["b", 2, None],
        ["c", 3, "=B5"],                     # original row 5, between the deletions
        ["d", 4, None],
        [None, None, None],                  # row 7: blank (deleted)
        ["e", 5, None],
    ]})
    if report is not None:
        check("separated deletions: a formula between them is flagged", shifted_cells(report) == {"C4"}, str(sorted(shifted_cells(report))))
        notes = shifted_notes(report, "Sheet")
        check(
            "separated deletions: the sheet note says the deletion started at original row 3",
            len(notes) == 1 and "starting at original row 3" in notes[0]["reason"],
            json.dumps(notes),
        )

    # K: the cap. 30 shifted formulas: 25 listed one by one, then one summary
    # flag saying 5 more.
    rows_k = [["Item", "Amt", "Ref"], [None, None, None]]     # row 2 is the deleted blank row
    rows_k += [["x", 1, f"=B{r}"] for r in range(3, 33)]      # 30 formulas, each pointing at its own old row
    report, _ = run_fixture(tmp, "flag_cap", {"Sheet": rows_k})
    if report is not None:
        check("flag cap: exactly 25 formulas are listed individually", len(shifted_cells(report)) == 25, str(len(shifted_cells(report))))
        summary = [f for f in shifted_notes(report, "Sheet") if "more formula" in f["reason"]]
        check("flag cap: one summary flag says 5 more", len(summary) == 1 and summary[0]["reason"].startswith("5 more formula"), json.dumps(summary))

    # L: things that look like references but are not. Deletion at row 3. All
    # of these point only at row 2 or at nothing, so none may be flagged:
    # LOG10( is a function, "Q4" is text, TOTAL9 is a longer word. The last
    # row is a real shifted reference, so this cannot pass by flagging nothing.
    report, _ = run_fixture(tmp, "not_references", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, "=LOG10(B2)"],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, '="Q4"&B2'],
        ["c", 3, "=TOTAL9*B2"],
        ["d", 4, "=B7"],                     # original row 7: a genuine shifted reference
    ]})
    if report is not None:
        check(
            "not-references: only the genuine shifted reference is flagged",
            shifted_cells(report) == {"C5"},
            str(sorted(shifted_cells(report))),
        )

    # R: a range that starts above the deletion and ends below it, and an
    # absolute reference. Both point at or below row 3, so both are flagged.
    report, _ = run_fixture(tmp, "straddle_absolute", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, "=SUM(B2:B9)"],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, "=$B$5"],
    ]})
    if report is not None:
        check("straddling range and absolute reference are both flagged", shifted_cells(report) == {"C2", "C3"}, str(sorted(shifted_cells(report))))

    # M: two sheets, references resolved against the sheet they point at. Only
    # "Q3 Detail" loses a row. Summary's total sums a range on Detail (flagged),
    # Summary's =...!B2 points above the deletion (not), and Summary's own
    # =B3*2 is on a sheet that lost nothing (not). Detail's =Summary!B3 points
    # at Summary, which lost nothing, so it must NOT be flagged even though row
    # 3 is Detail's own deleted row. The note appears once on Detail, never on
    # Summary.
    report, _ = run_fixture(tmp, "two_sheets", {
        "Summary": [
            ["Line", "Value"],
            ["Total", "=SUM('Q3 Detail'!B4:B6)"],
            ["Head", "='Q3 Detail'!B2"],
            ["Own", "=B3*2"],
        ],
        "Q3 Detail": [
            ["Item", "Amt", "Back"],
            ["a", 1, "=Summary!B3"],
            [None, None, None],              # row 3: blank divider (deleted)
            ["b", 2, None], ["c", 3, None], ["d", 4, None],
        ],
    })
    if report is not None:
        check("two sheets: Summary's total over the changed sheet is flagged, its other formulas are not",
              shifted_cells(report, "Summary") == {"B2"}, str(sorted(shifted_cells(report, "Summary"))))
        check("two sheets: Detail's reference to an unchanged sheet is not flagged",
              shifted_cells(report, "Q3 Detail") == set(), str(sorted(shifted_cells(report, "Q3 Detail"))))
        check("two sheets: the sheet note appears exactly once on the sheet that lost a row",
              len(shifted_notes(report, "Q3 Detail")) == 1, json.dumps(shifted_notes(report, "Q3 Detail")))
        check("two sheets: no sheet note on the sheet that lost nothing",
              shifted_notes(report, "Summary") == [], json.dumps(shifted_notes(report, "Summary")))

    # N: array and data-table formulas. openpyxl returns these as objects, not
    # "=..." strings. A stale array formula must be flagged; a data table on a
    # sheet that lost a row is flagged outright.
    from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula
    report, _ = run_fixture(tmp, "array_formula", {"Sheet": [
        ["Item", "Amt", "Arr"],
        ["a", 1, None],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, ArrayFormula("C4", "=SUM(B4:B5)")],
        ["c", 3, None],
    ]})
    if report is not None:
        check("array formula: a stale array formula is flagged", shifted_cells(report) == {"C3"}, str(sorted(shifted_cells(report))))
    report, _ = run_fixture(tmp, "data_table", {"Sheet": [
        ["Item", "Amt", "Tbl"],
        ["a", 1, None],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, DataTableFormula(ref="C4:C5", dt2D=False, dtr=False, r1="A1")],
        ["c", 3, None],
    ]})
    if report is not None:
        check("data table: flagged outright on a sheet that lost a row", shifted_cells(report) == {"C3"}, str(sorted(shifted_cells(report))))

    # O: INDIRECT and OFFSET build their target at run time. Flagged on a sheet
    # that lost a row. The word inside quotes is text, not a call.
    report, _ = run_fixture(tmp, "dynamic_refs", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, '=INDIRECT("B"&6)'],
        ["b", 2, "=OFFSET(B2,1,0)"],
        [None, None, None],                  # row 4: blank divider (deleted)
        ["c", 3, '="OFFSET("&B2'],
    ]})
    if report is not None:
        check("dynamic refs: INDIRECT and OFFSET formulas are flagged, the quoted word is not",
              shifted_cells(report) == {"C2", "C3"}, str(sorted(shifted_cells(report))))

    # P: --detect-only runs none of the cleaning rules, so it reports none of
    # the defect flags either, only hidden/protected sheets and external links.
    report, cleaned = run_fixture(tmp, "detect_only", {"Sheet": [
        ["Category", "Amount"],
        ["Total", "=SUM(B4:B6)"],
        [None, None],
        ["A", 10], ["B", 20], ["C", 30],
    ]}, extra_args=["--detect-only"])
    if report is not None:
        check("detect-only: no changes and no flags for a defect-only workbook",
              report.get("changes", []) == [] and report.get("flags", []) == [], json.dumps(report))
        check("detect-only: no cleaned copy is written", not os.path.isfile(cleaned))

    # S: a formula holding a run of thousands of digits (a crafted or corrupt
    # cell). Under Python 3.11+ int() on more than 4,300 digits raises, which
    # used to stop the whole cleanup with exit 2 and no output. It is not a
    # cell reference (Excel's last row has 7 digits), so it is ignored, and
    # the real shifted reference beside it is still flagged. (Python 3.9,
    # which has no such limit, passes this either way; CI runs 3.12.)
    report, _ = run_fixture(tmp, "huge_digit_run", {"Sheet": [
        ["Item", "Amt", "Ref"],
        ["a", 1, "=A" + "1" * 5000],
        [None, None, None],                  # row 3: blank divider (deleted)
        ["b", 2, "=B3"],
    ]})
    if report is not None:
        check("huge digit run: ignored, and the genuine shifted reference is still flagged",
              shifted_cells(report) == {"C3"}, str(sorted(shifted_cells(report))))


# ---------------------------------------------------------------------------
# Criterion 4: clean-control.xlsx produces an empty report and exits 0.
# ---------------------------------------------------------------------------

def eval_clean_control(tmp):
    src = os.path.join(FIXTURES, "clean-control.xlsx")
    out_dir = os.path.join(tmp, "clean_control_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(src, out_dir)
    check("clean-control.xlsx: clean.py exits 0", res.returncode == 0, res.stderr)
    report = load_report(out_dir, src)
    check("clean-control.xlsx: report was written", report is not None)
    if report is not None:
        check("clean-control.xlsx: change report is empty", report.get("changes") == [], json.dumps(report))


# ---------------------------------------------------------------------------
# Criterion 5: fidelity.xlsx keeps its formula, date, and number format.
# ---------------------------------------------------------------------------

def eval_fidelity(tmp):
    import openpyxl

    src = os.path.join(FIXTURES, "fidelity.xlsx")
    out_dir = os.path.join(tmp, "fidelity_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(src, out_dir)
    check("fidelity.xlsx: clean.py exits 0", res.returncode == 0, res.stderr)

    cleaned_path = os.path.join(out_dir, "fidelity.cleaned.xlsx")
    check("fidelity.xlsx: cleaned copy was written", os.path.isfile(cleaned_path))
    if not os.path.isfile(cleaned_path):
        return

    wb = openpyxl.load_workbook(cleaned_path, data_only=False)
    ws = wb["Fidelity"]
    check("fidelity.xlsx: B1 keeps formula =1+1", ws["B1"].value == "=1+1", repr(ws["B1"].value))
    check("fidelity.xlsx: B2 keeps date type", hasattr(ws["B2"].value, "year"))
    check("fidelity.xlsx: B2 keeps yyyy-mm-dd format", ws["B2"].number_format == "yyyy-mm-dd", ws["B2"].number_format)
    check("fidelity.xlsx: B3 keeps currency format", ws["B3"].number_format == '"$"#,##0.00', ws["B3"].number_format)


# ---------------------------------------------------------------------------
# Criterion 6: .xlsm input is refused (exit 2), no output written.
# ---------------------------------------------------------------------------

def build_macro_workbook(tmp, path, macro_part_name="xl/vbaProject.bin"):
    import openpyxl

    src_xlsx = os.path.join(tmp, os.path.basename(path) + ".src.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "hello"
    wb.save(src_xlsx)

    shutil.copyfile(src_xlsx, path)
    # Append the macro part so the gate's macro check has something real to
    # catch. Callers can pass a non-default macro_part_name to exercise the
    # broadened matching (case, xl/macrosheets/, xl/activeX/) rather than
    # only the one exact literal path.
    with zipfile.ZipFile(path, "a") as zf:
        zf.writestr(macro_part_name, b"\x00" * 32)
    return path


def eval_xlsm(tmp):
    # Case A: a genuine .xlsm extension. This is refused by the extension
    # check alone, before the macro-part check ever runs — kept for
    # completeness, but it does not prove the macro-part check works.
    xlsm_path = build_macro_workbook(tmp, os.path.join(tmp, "macro.xlsm"))
    out_dir = os.path.join(tmp, "xlsm_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(xlsm_path, out_dir)
    check(".xlsm input: clean.py exits 2", res.returncode == 2, f"stdout={res.stdout} stderr={res.stderr}")
    written = os.listdir(out_dir)
    check(".xlsm input: no output file is written", written == [], str(written))

    # Case B: the actual gap the macro-part check exists for — a macro part
    # smuggled into a file saved with a plain .xlsx extension, so the
    # extension check can't be the thing that catches it.
    renamed_path = build_macro_workbook(tmp, os.path.join(tmp, "macro_renamed.xlsx"))
    out_dir_b = os.path.join(tmp, "xlsm_renamed_out")
    os.makedirs(out_dir_b, exist_ok=True)
    res_b = run_clean(renamed_path, out_dir_b)
    check(
        "macro part under a .xlsx extension: clean.py exits 2",
        res_b.returncode == 2,
        f"stdout={res_b.stdout} stderr={res_b.stderr}",
    )
    check("macro part under .xlsx: stderr names the macro part", "macro" in res_b.stderr.lower(), res_b.stderr)
    check(
        "macro part under .xlsx: no output file is written",
        os.listdir(out_dir_b) == [],
        str(os.listdir(out_dir_b)),
    )

    # Case C: coverage for _is_macro_part()'s case-insensitive matching.
    # The ORIGINAL gate (before the review that added _is_macro_part) only
    # matched the exact literal "xl/vbaProject.bin" (case-sensitive
    # equality), so a differently-cased part would have slipped through
    # unrefused. _is_macro_part() has been case-insensitive since it was
    # introduced, so this case passes on every commit from that point on —
    # it's a real assertion against the current behavior, not a
    # regression test distinguishing any two specific commits since then.
    cased_path = build_macro_workbook(
        tmp, os.path.join(tmp, "macro_cased.xlsx"), macro_part_name="xl/VBAProject.BIN"
    )
    out_dir_c = os.path.join(tmp, "xlsm_cased_out")
    os.makedirs(out_dir_c, exist_ok=True)
    res_c = run_clean(cased_path, out_dir_c)
    check(
        "differently-cased macro part: clean.py exits 2",
        res_c.returncode == 2,
        f"stdout={res_c.stdout} stderr={res_c.stderr}",
    )
    check(
        "differently-cased macro part: no output file is written",
        os.listdir(out_dir_c) == [],
        str(os.listdir(out_dir_c)),
    )


# ---------------------------------------------------------------------------
# Criterion 7: hidden sheet / protected sheet / external link are flagged,
# not changed.
# ---------------------------------------------------------------------------

def build_hidden_sheet_wb(tmp):
    import openpyxl

    path = os.path.join(tmp, "hidden.xlsx")
    wb = openpyxl.Workbook()
    wb.active.title = "Visible"
    wb.active["A1"] = "ok"
    hidden = wb.create_sheet("Hidden")
    hidden["A1"] = "secret"
    hidden.sheet_state = "hidden"
    wb.save(path)
    return path


def build_protected_sheet_wb(tmp):
    import openpyxl
    from openpyxl.worksheet.protection import SheetProtection

    path = os.path.join(tmp, "protected.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Protected"
    ws["A1"] = "locked down"
    ws.protection = SheetProtection(sheet=True)
    wb.save(path)
    return path


def build_external_link_wb(tmp):
    import openpyxl

    src_path = os.path.join(tmp, "external_src.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "=[1]Sheet1!A1"
    wb.save(src_path)

    ext_path = os.path.join(tmp, "external.xlsx")
    shutil.copyfile(src_path, ext_path)
    with zipfile.ZipFile(ext_path, "a") as zf:
        zf.writestr(
            "xl/externalLinks/externalLink1.xml",
            '<?xml version="1.0"?><externalLink xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )
    return ext_path


def eval_hidden_protected_external(tmp):
    for label, builder in (
        ("hidden sheet", build_hidden_sheet_wb),
        ("protected sheet", build_protected_sheet_wb),
        ("external link", build_external_link_wb),
    ):
        src = builder(tmp)
        out_dir = os.path.join(tmp, label.replace(" ", "_") + "_out")
        os.makedirs(out_dir, exist_ok=True)
        res = run_clean(src, out_dir)
        check(f"{label}: clean.py exits 0 (flag, not refusal)", res.returncode == 0, res.stderr)
        report = load_report(out_dir, src)
        check(f"{label}: report was written", report is not None)
        if report is not None:
            rules = {fl.get("rule") for fl in report.get("flags", [])}
            expected_rule = {
                "hidden sheet": "hidden_sheet",
                "protected sheet": "protected_sheet",
                "external link": "external_link",
            }[label]
            check(
                f"{label}: flagged under rule {expected_rule!r}",
                expected_rule in rules,
                json.dumps(report),
            )


# ---------------------------------------------------------------------------
# Extra guard cases named in the plan: oversized file, XML entity expansion,
# path traversal via a crafted input filename.
# ---------------------------------------------------------------------------

def eval_oversized(tmp):
    import openpyxl

    path = os.path.join(tmp, "big.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "x"
    wb.save(path)

    # Pad the zip with an oversized extra member so the file crosses 25MB
    # without needing real spreadsheet content.
    padded_path = os.path.join(tmp, "big_padded.xlsx")
    shutil.copyfile(path, padded_path)
    with zipfile.ZipFile(padded_path, "a", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("xl/padding.bin", b"\x00" * (26 * 1024 * 1024))

    out_dir = os.path.join(tmp, "big_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(padded_path, out_dir)
    check("oversized file (>25MB): clean.py exits 2", res.returncode == 2, f"stdout={res.stdout} stderr={res.stderr}")
    check("oversized file: stderr names the 25MB limit", "25MB" in res.stderr, res.stderr)
    check("oversized file: no output written", os.listdir(out_dir) == [], str(os.listdir(out_dir)))


def eval_entity_expansion(tmp):
    import openpyxl

    path = os.path.join(tmp, "bomb_src.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "hello"
    wb.save(path)

    bomb_payload = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<!DOCTYPE sst [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>'
        b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">'
        b"<si><t>&lol2;</t></si></sst>"
    )
    bomb_path = os.path.join(tmp, "bomb.xlsx")
    with zipfile.ZipFile(path) as src_zf:
        names = src_zf.namelist()
        with zipfile.ZipFile(bomb_path, "w") as out_zf:
            wrote_shared_strings = False
            for name in names:
                data = src_zf.read(name)
                if name == "xl/sharedStrings.xml":
                    data = bomb_payload
                    wrote_shared_strings = True
                out_zf.writestr(name, data)
            if not wrote_shared_strings:
                # This openpyxl version inlines strings and never wrote a
                # sharedStrings.xml part of its own; add one carrying the
                # entity-expansion payload directly, which is enough to prove
                # defusedxml (not openpyxl's own parser) is the one reading it.
                out_zf.writestr("xl/sharedStrings.xml", bomb_payload)

    out_dir = os.path.join(tmp, "bomb_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(bomb_path, out_dir)
    check(
        "entity-expansion payload: clean.py exits 2 without expanding it",
        res.returncode == 2,
        f"stdout={res.stdout} stderr={res.stderr}",
    )
    # Asserting the NEW wording ("XML construct") rather than just
    # "forbidden" is deliberate: with defusedxml's default parser settings
    # (forbid_entities=True), EntityDeclHandler intercepts every entity
    # declaration before ExternalEntityRefHandler is ever reached, so
    # EntitiesForbidden is the only exception this attack shape can
    # actually raise — a payload distinguishing "only EntitiesForbidden is
    # caught" from "any DefusedXmlException is caught" isn't constructible
    # against this library's defaults. What DID change between the two
    # versions of clean.py is the refusal message itself: the pre-fix
    # handler said "...a forbidden XML entity payload" (no "construct"
    # substring); the fix's broader `except DefusedXmlException` handler
    # says "...a forbidden XML construct (...)". This assertion is real
    # regression coverage for that wording change, even though it can't
    # exercise the broadened exception type directly.
    check(
        "entity-expansion payload: stderr names the forbidden construct (not a generic error)",
        "xml construct" in res.stderr.lower(),
        res.stderr,
    )
    check(
        "entity-expansion payload: no output file is left behind on refusal",
        os.listdir(out_dir) == [],
        str(os.listdir(out_dir)),
    )


def eval_path_traversal(tmp):
    import openpyxl

    src_dir = os.path.join(tmp, "traversal_src")
    os.makedirs(src_dir, exist_ok=True)
    out_dir = os.path.join(tmp, "traversal_out")
    os.makedirs(out_dir, exist_ok=True)

    # Case A: a filename whose stem, if used unsanitized, would climb out of
    # out_dir via a literal ".." path segment. stem_from_input() collapses
    # any path separator in the basename to "_" first, so this can only ever
    # test the "..str.." substring guard, not a real directory escape — kept
    # for that guard's own sake.
    crafted_path = os.path.join(src_dir, "..evil..xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "x"
    wb.save(crafted_path)

    res = run_clean(crafted_path, out_dir)
    check("crafted filename: clean.py exits 0", res.returncode == 0, res.stderr)
    out_dir_real = os.path.realpath(out_dir)
    written = sorted(os.listdir(out_dir))
    check(
        "crafted filename: exact expected output names, no extras",
        written == ["_evil..changes.json", "_evil..cleaned.xlsx"],
        str(written),
    )
    for name in written:
        full = os.path.realpath(os.path.join(out_dir, name))
        check(
            f"crafted filename: written file {name!r} resolves inside the output dir",
            os.path.commonpath([out_dir_real, full]) == out_dir_real,
        )

    # Case B: prove safe_output_path()'s symlink guard by planting a
    # symlink at the EXACT output path clean.py will try to write to, then
    # asserting it's refused rather than followed. The decoy target lives
    # INSIDE real_target on purpose — a symlink pointing entirely outside
    # out_dir is already caught by the pre-existing commonpath containment
    # check (see Case A), which would make this case pass even with the
    # newer islink() guard deleted, proving nothing about it.
    real_target = os.path.join(tmp, "traversal_real_target")
    os.makedirs(real_target, exist_ok=True)
    probe_link = os.path.join(real_target, "symlink_probe")
    try:
        os.symlink(os.path.join(real_target, "probe_target"), probe_link)
        os.remove(probe_link)
        symlink_supported = True
    except (OSError, NotImplementedError):
        symlink_supported = False

    if not symlink_supported:
        print("[SKIP] pre-existing symlink at the output path: symlinks unsupported on this host")
    else:
        normal_src = os.path.join(src_dir, "normal.xlsx")
        wb2 = openpyxl.Workbook()
        wb2.active["A1"] = "x"
        wb2.save(normal_src)
        decoy_path = os.path.join(real_target, "decoy.xlsx")
        with open(decoy_path, "wb") as f:
            f.write(b"decoy content, must survive untouched")
        pre_existing_link = os.path.join(real_target, "normal.cleaned.xlsx")
        os.symlink(decoy_path, pre_existing_link)

        res_b = run_clean(normal_src, real_target)
        check(
            "pre-existing symlink at the output path: clean.py refuses (exit 2)",
            res_b.returncode == 2,
            f"stdout={res_b.stdout} stderr={res_b.stderr}",
        )
        check(
            "pre-existing symlink at the output path: stderr names the symlink",
            "symlink" in res_b.stderr.lower(),
            res_b.stderr,
        )
        with open(decoy_path, "rb") as f:
            decoy_after = f.read()
        check(
            "pre-existing symlink at the output path: the symlink's target is untouched",
            decoy_after == b"decoy content, must survive untouched",
            repr(decoy_after),
        )
        leftover = sorted(
            n for n in os.listdir(real_target)
            if n not in ("normal.cleaned.xlsx", "decoy.xlsx")
        )
        check(
            "pre-existing symlink at the output path: no stray temp file left behind",
            leftover == [],
            str(leftover),
        )


def eval_failure_does_not_delete_prior_output(tmp):
    """
    A later run that fails for an unrelated reason must never delete a
    ".cleaned.xlsx" a PREVIOUS, successful run already wrote at that same
    path. An earlier version of clean.py deleted "cleaned_path" in its
    failure handler whenever the CURRENT run hadn't (yet) finished writing
    it, which silently destroyed a good file from an earlier run any time
    a later, unrelated run over the same output folder failed.
    """
    import openpyxl

    out_dir = os.path.join(tmp, "prior_output_out")
    os.makedirs(out_dir, exist_ok=True)

    good_src = os.path.join(tmp, "good.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "x"
    wb.save(good_src)

    res1 = run_clean(good_src, out_dir)
    check("prior-output setup: first run exits 0", res1.returncode == 0, res1.stderr)
    cleaned_path = os.path.join(out_dir, "good.cleaned.xlsx")
    check("prior-output setup: first run wrote a cleaned copy", os.path.isfile(cleaned_path))
    if not os.path.isfile(cleaned_path):
        return
    with open(cleaned_path, "rb") as f:
        good_output_bytes = f.read()

    # Now run again with the SAME stem (same input basename "good.xlsx", so
    # the same cleaned_path) but a second input that fails check_sheet_size
    # AFTER the workbook loads and BEFORE this run's own wb.save() ever
    # runs. This is the actual shape the original bug needed: a Refusal
    # raised at the very top of the function (like the oversized-file-size
    # gate) never reached the old failure-cleanup handler at all, since it
    # ran before that function's try block even opened — using that kind of
    # failure here would pass even against the buggy code, for the wrong
    # reason. A failure that happens once the workbook is loaded and
    # cleaning is under way (check_sheet_size refusing, a rule raising) is
    # what actually exercises the cleanup handler, with out_dir itself
    # fully writable throughout — otherwise the old bug's own delete call
    # would fail too, for an unrelated reason, and mask what's being tested.
    second_src_dir = os.path.join(tmp, "prior_output_second_src")
    os.makedirs(second_src_dir, exist_ok=True)
    second_src = os.path.join(second_src_dir, "good.xlsx")
    wb2 = openpyxl.Workbook()
    ws2 = wb2.active
    ws2["A1"] = "x"
    ws2.cell(row=1_048_576, column=2).value = "y"  # forces max_row*max_col over the 2,000,000 cap
    wb2.save(second_src)

    res2 = run_clean(second_src, out_dir)
    # Assert the specific refusal, not just "some failure happened" — a
    # loosely-worded check here could keep passing even if a change moved
    # this input to fail some OTHER, earlier gate instead of check_sheet_size,
    # silently stopping this from testing what it claims to.
    check("prior-output: second (oversized-dimensions) run exits 2", res2.returncode == 2, res2.stderr)
    check(
        "prior-output: second run's stderr names the cell-count cap",
        "cells" in res2.stderr and "2000000" in res2.stderr,
        res2.stderr,
    )
    check(
        "prior-output: first run's cleaned copy still exists after the second run fails",
        os.path.isfile(cleaned_path),
    )
    if os.path.isfile(cleaned_path):
        with open(cleaned_path, "rb") as f:
            after_bytes = f.read()
        check(
            "prior-output: first run's cleaned copy is byte-identical after the second run fails",
            after_bytes == good_output_bytes,
        )


def run_eval(fn, tmp):
    """Run one eval; if it crashes (say, a full disk), record a FAIL and carry on, so
    one broken eval can't silently skip every eval after it."""
    try:
        fn(tmp)
    except Exception as e:
        check(f"{fn.__name__} ran to completion", False, f"{type(e).__name__}: {e}")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        # The two that write ~26 MB files run last.
        for fn in (
            eval_messy, eval_clean_control, eval_fidelity, eval_xlsm,
            eval_hidden_protected_external, eval_entity_expansion, eval_path_traversal,
            eval_flag_only_edge_cases, eval_oversized, eval_failure_does_not_delete_prior_output,
        ):
            run_eval(fn, tmp)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

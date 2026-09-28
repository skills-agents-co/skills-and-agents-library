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
    # Insurance) shift up by two, so their surviving D-column formulas are now
    # stale — they still literally reference their pre-deletion row numbers
    # (=SUM(B9:C9) etc. sitting at row 7). Since restore_column_formula no
    # longer re-anchors ANYTHING, this staleness must be reported as a flag
    # instead of silently left with no signal at all — check that here,
    # separately from the byte-identity check above (which only proves the
    # cell wasn't rewritten, not that its staleness was noticed).
    flags_before_defect_check = report.get("flags", [])
    stale_flags_by_range = {
        f["range"]: f
        for f in flags_before_defect_check
        if f["rule"] == "restore_column_formula" and "stale" in f["reason"]
    }
    for label in ("Travel", "Software", "Insurance"):
        cell = ws.cell(row=cleaned_rows_by_cat[label], column=4)
        check(
            f"messy.xlsx: {label}'s now-stale D-column formula is flagged (row shifted, formula wasn't re-anchored)",
            cell.coordinate in stale_flags_by_range,
            f"flags seen: {[f['range'] for f in flags_before_defect_check if f['rule'] == 'restore_column_formula']}",
        )
    for label in ("Rent", "Utilities", "Payroll"):
        # These rows sit ABOVE the deletion and never shift, so their formulas
        # were never stale and must NOT be flagged.
        cell = ws.cell(row=cleaned_rows_by_cat[label], column=4)
        check(
            f"messy.xlsx: {label}'s D-column formula (never shifted) is not flagged as stale",
            cell.coordinate not in stale_flags_by_range,
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


def eval_flag_only_edge_cases(tmp):
    """
    The other two flag paths in restore_column_formula and
    unpivot_date_columns — inconsistent formula shapes, and a formula
    referencing the month block as a block range — predate this task and had
    no eval coverage at all before it. This task's own edits sit directly
    around both, so cover them now.
    """
    import openpyxl

    # Case A: a column of formulas with no single consistent shape, plus a
    # literal cell. Must be flagged as "multiple formula shapes", and the
    # literal must be left completely untouched.
    path = os.path.join(tmp, "mixed_shapes.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet"
    ws.append(["Category", "B", "C", "Total"])
    ws.append(["Rent", 100, 5, "=B2+C2"])
    ws.append(["Utilities", 200, 3, "=B3*C3"])  # different shape on purpose
    ws.append(["Payroll", 300, 2, 999])  # the literal that should stay untouched
    wb.save(path)

    out_dir = os.path.join(tmp, "mixed_shapes_out")
    os.makedirs(out_dir, exist_ok=True)
    res = run_clean(path, out_dir)
    check("mixed formula shapes: clean.py exits 0", res.returncode == 0, res.stderr)
    report = load_report(out_dir, path)
    check("mixed formula shapes: report was written", report is not None)
    if report is not None:
        flags = report.get("flags", [])
        check(
            "mixed formula shapes: flagged as 'column has multiple formula shapes'",
            any(
                f["rule"] == "restore_column_formula" and "multiple formula shapes" in f["reason"]
                for f in flags
            ),
            json.dumps(flags),
        )
        check(
            "mixed formula shapes: no change entries for restore_column_formula",
            not any(c["rule"] == "restore_column_formula" for c in report.get("changes", [])),
            json.dumps(report.get("changes", [])),
        )
    cleaned_path = os.path.join(out_dir, "mixed_shapes.cleaned.xlsx")
    if os.path.isfile(cleaned_path):
        wb_out = openpyxl.load_workbook(cleaned_path, data_only=False)
        d4 = wb_out["Sheet"].cell(row=4, column=4).value
        check("mixed formula shapes: the literal cell is untouched (still 999)", d4 == 999, repr(d4))

    # Case B: month columns where another formula references the month block
    # as a range (e.g. a grand-total elsewhere). Must be flagged as
    # "references this range as a block", and the sheet must be untouched.
    # total_col only exists (and only then does the block-reference guard
    # ever run) when the month block doesn't already reach the sheet's last
    # column, so this fixture needs a trailing column past Feb-2026 — and the
    # block-referencing formula has to sit outside that trailing column
    # (which the guard explicitly excludes as "the Total-like column"), so
    # it's placed in column A instead.
    path_b = os.path.join(tmp, "block_ref.xlsx")
    wb_b = openpyxl.Workbook()
    ws_b = wb_b.active
    ws_b.title = "Sheet"
    ws_b.append(["Category", "Jan-2026", "Feb-2026", "Total"])
    ws_b.append(["Rent", 100, 200, "=B2+C2"])
    ws_b.append(["Utilities", 150, 250, "=B3+C3"])
    ws_b.append(["=SUM(B2:C3)", None, None, None])  # references the month block as a range
    wb_b.save(path_b)

    out_dir_b = os.path.join(tmp, "block_ref_out")
    os.makedirs(out_dir_b, exist_ok=True)
    res_b = run_clean(path_b, out_dir_b)
    check("block-referenced months: clean.py exits 0", res_b.returncode == 0, res_b.stderr)
    report_b = load_report(out_dir_b, path_b)
    check("block-referenced months: report was written", report_b is not None)
    if report_b is not None:
        flags_b = report_b.get("flags", [])
        check(
            "block-referenced months: flagged as 'references this range as a block'",
            any(
                f["rule"] == "unpivot_date_columns" and "references this range as a block" in f["reason"]
                for f in flags_b
            ),
            json.dumps(flags_b),
        )
        check(
            "block-referenced months: no change entries for unpivot_date_columns",
            not any(c["rule"] == "unpivot_date_columns" for c in report_b.get("changes", [])),
            json.dumps(report_b.get("changes", [])),
        )
    cleaned_path_b = os.path.join(out_dir_b, "block_ref.cleaned.xlsx")
    if os.path.isfile(cleaned_path_b):
        wb_out_b = openpyxl.load_workbook(cleaned_path_b, data_only=False)
        ws_out_b = wb_out_b["Sheet"]
        headers_b = [ws_out_b.cell(row=1, column=c).value for c in range(1, 5)]
        check(
            "block-referenced months: header unchanged (not unpivoted)",
            headers_b == ["Category", "Jan-2026", "Feb-2026", "Total"],
            str(headers_b),
        )

    # Case C (#F1 regression): an ALL-formula column, with no literal cell at
    # all, below a deleted blank/duplicate-header row pair. The stale-row
    # check must not be gated on a literal being present in the column —
    # this fixture has none — or a wrong total ships with zero signal.
    path_c = os.path.join(tmp, "all_formula_stale.xlsx")
    wb_c = openpyxl.Workbook()
    ws_c = wb_c.active
    ws_c.title = "Sheet"
    ws_c.append(["Category", "B", "C", "Total"])  # row 1: header
    ws_c.append(["A", 10, 1, "=B2+C2"])            # row 2: above the deletion, never shifts
    ws_c.append([None, None, None, None])          # row 3: blank divider (deleted)
    ws_c.append(["Category", "B", "C", "Total"])   # row 4: duplicate header (deleted)
    ws_c.append(["Bee", 20, 2, "=B5+C5"])           # row 5 -> shifts to row 3, stale
    ws_c.append(["Cee", 30, 3, "=B6+C6"])           # row 6 -> shifts to row 4, stale
    wb_c.save(path_c)

    out_dir_c2 = os.path.join(tmp, "all_formula_stale_out")
    os.makedirs(out_dir_c2, exist_ok=True)
    res_c = run_clean(path_c, out_dir_c2)
    check("all-formula stale column: clean.py exits 0", res_c.returncode == 0, res_c.stderr)
    report_c = load_report(out_dir_c2, path_c)
    check("all-formula stale column: report was written", report_c is not None)
    if report_c is not None:
        flags_c = report_c.get("flags", [])
        stale_ranges_c = {
            f["range"] for f in flags_c
            if f["rule"] == "restore_column_formula" and "stale" in f["reason"]
        }
        check(
            "all-formula stale column: D3 (was row 5) is flagged stale",
            "D3" in stale_ranges_c,
            json.dumps(flags_c),
        )
        check(
            "all-formula stale column: D4 (was row 6) is flagged stale",
            "D4" in stale_ranges_c,
            json.dumps(flags_c),
        )
        check(
            "all-formula stale column: D2 (never shifted) is NOT flagged stale",
            "D2" not in stale_ranges_c,
            json.dumps(flags_c),
        )
        check(
            "all-formula stale column: no change entries for restore_column_formula",
            not any(c["rule"] == "restore_column_formula" for c in report_c.get("changes", [])),
            json.dumps(report_c.get("changes", [])),
        )
    cleaned_path_c = os.path.join(out_dir_c2, "all_formula_stale.cleaned.xlsx")
    if os.path.isfile(cleaned_path_c):
        wb_out_c = openpyxl.load_workbook(cleaned_path_c, data_only=False)
        ws_out_c = wb_out_c["Sheet"]
        check(
            "all-formula stale column: D3's formula is byte-identical to input's D5 (not rewritten)",
            ws_out_c.cell(row=3, column=4).value == "=B5+C5",
            repr(ws_out_c.cell(row=3, column=4).value),
        )
        check(
            "all-formula stale column: D4's formula is byte-identical to input's D6 (not rewritten)",
            ws_out_c.cell(row=4, column=4).value == "=B6+C6",
            repr(ws_out_c.cell(row=4, column=4).value),
        )


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


def main():
    with tempfile.TemporaryDirectory() as tmp:
        eval_messy(tmp)
        eval_clean_control(tmp)
        eval_fidelity(tmp)
        eval_xlsm(tmp)
        eval_hidden_protected_external(tmp)
        eval_oversized(tmp)
        eval_entity_expansion(tmp)
        eval_path_traversal(tmp)
        eval_failure_does_not_delete_prior_output(tmp)
        eval_flag_only_edge_cases(tmp)

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

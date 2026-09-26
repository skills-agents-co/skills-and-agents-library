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

    # Defect 1: merged header gone.
    check("messy.xlsx: A1:D1 no longer merged", "A1:D1" not in {str(r) for r in ws.merged_cells.ranges})

    # Defect 2: month columns unpivoted into one date column.
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
        "messy.xlsx: month columns collapsed into a single Date column",
        header_row is not None and "Date" in header_vals and "Jan-2026" not in header_vals and "Feb-2026" not in header_vals,
        str(header_vals),
    )

    import datetime as _dt
    date_col = None
    amount_col = None
    if header_row:
        for c, v in enumerate(header_vals, start=1):
            if v == "Date":
                date_col = c
            if v == "Amount":
                amount_col = c
    dates_found = set()
    amounts_found = []
    if date_col and amount_col:
        for r in range(header_row + 1, ws.max_row + 1):
            dv = ws.cell(row=r, column=date_col).value
            av = ws.cell(row=r, column=amount_col).value
            if isinstance(dv, _dt.datetime):
                dates_found.add((dv.year, dv.month))
            if av is not None:
                amounts_found.append(av)
    check(
        "messy.xlsx: unpivoted rows carry real Jan/Feb 2026 dates",
        dates_found == {(2026, 1), (2026, 2)},
        str(dates_found),
    )

    # Defect 3: text-stored numbers converted to real numbers with the right values.
    check(
        "messy.xlsx: former text amounts 1000/1200/2200 are now numeric",
        all(isinstance(v, (int, float)) for v in amounts_found) and
        {1000, 1200, 2200}.issubset({v for v in amounts_found if isinstance(v, (int, float))}),
        str(amounts_found),
    )

    # Defect 5: every Total-like formula cell shares one relative shape (no hardcode left).
    total_col = None
    if header_row:
        for c, v in enumerate(header_vals, start=1):
            if v == "Total":
                total_col = c
    total_vals = []
    if total_col:
        for r in range(header_row + 1, ws.max_row + 1):
            v = ws.cell(row=r, column=total_col).value
            if v is not None:
                total_vals.append(v)
    check(
        "messy.xlsx: every Total cell is a formula (no hardcoded value survives)",
        total_col is not None and len(total_vals) > 0 and all(isinstance(v, str) and v.startswith("=") for v in total_vals),
        str(total_vals),
    )

    # Defect 6: blank divider row and duplicate header row are gone.
    all_rows = []
    for r in range(1, ws.max_row + 1):
        all_rows.append([ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)])
    blank_rows = [row for row in all_rows if all(v in (None, "") for v in row)]
    header_like_rows = [row for row in all_rows if row == header_vals]
    check("messy.xlsx: no fully-blank divider row remains", len(blank_rows) == 0, str(all_rows))
    check("messy.xlsx: no repeated header row remains", len(header_like_rows) <= 1, str(all_rows))

    # Every manifest defect maps to at least one report entry.
    defect_ids = [d["id"] for d in manifest["messy"]["defects"]]
    rules_seen = {c["rule"] for c in changes}
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
        check(
            f"messy.xlsx: manifest defect '{defect_id}' has a matching report entry",
            expected_rule in rules_seen,
            f"rules seen: {rules_seen}",
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

def build_macro_workbook(tmp, path):
    import openpyxl

    src_xlsx = os.path.join(tmp, os.path.basename(path) + ".src.xlsx")
    wb = openpyxl.Workbook()
    wb.active["A1"] = "hello"
    wb.save(src_xlsx)

    shutil.copyfile(src_xlsx, path)
    # Append a vbaProject.bin part so the gate's macro check has something real to catch.
    with zipfile.ZipFile(path, "a") as zf:
        zf.writestr("xl/vbaProject.bin", b"\x00" * 32)
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
    check(
        "entity-expansion payload: stderr names the forbidden construct (not a generic error)",
        "forbidden" in res.stderr.lower(),
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

    # Case B: prove the actual escape refusal (safe_output_path's commonpath
    # check) by pointing --out-dir at a symlink that resolves OUTSIDE the
    # directory the caller thinks they're writing into.
    real_target = os.path.join(tmp, "traversal_real_target")
    os.makedirs(real_target, exist_ok=True)
    outside_dir = os.path.join(tmp, "traversal_outside")
    os.makedirs(outside_dir, exist_ok=True)
    escape_link = os.path.join(outside_dir, "escape_link")
    try:
        os.symlink(real_target, escape_link)
        symlink_supported = True
    except (OSError, NotImplementedError):
        symlink_supported = False

    if symlink_supported:
        normal_src = os.path.join(src_dir, "normal.xlsx")
        wb2 = openpyxl.Workbook()
        wb2.active["A1"] = "x"
        wb2.save(normal_src)
        # Passing --out-dir as a path THROUGH the symlink is the ordinary,
        # supported case (realpath resolves it and the check passes) — this
        # is not the escape. The escape this guard exists for is a stem or
        # out_dir value that resolves outside of realpath(out_dir) itself,
        # which can't happen once out_dir is realpath'd first. What CAN
        # still happen is a symlink planted at the exact output path AFTER
        # the containment check runs — see clean.py's safe_output_path().
        # That race isn't reproducible deterministically in a black-box
        # eval, so this case instead asserts the documented mitigation is
        # present: an existing symlink AT the output path is refused outright.
        pre_existing_link = os.path.join(real_target, "normal.cleaned.xlsx")
        os.symlink(os.path.join(tmp, "some_other_file"), pre_existing_link)
        res_b = run_clean(normal_src, real_target)
        check(
            "pre-existing symlink at the output path: clean.py refuses (exit 2)",
            res_b.returncode == 2,
            f"stdout={res_b.stdout} stderr={res_b.stderr}",
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

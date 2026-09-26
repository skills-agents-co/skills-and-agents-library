---
name: "Spreadsheet Cleanup"
description: "Cleans up a messy finance spreadsheet automatically - fixes merged headers, split-out month columns, numbers stuck as text, and stray formulas, then hands you a clean copy plus a plain list of what changed."
longDescription: "Give it a .xlsx finance workbook and it writes a cleaned copy next to the original, never touching the file you gave it. It fixes five common spreadsheet defects by rule (merged header cells, months spread across separate columns instead of one date column, amounts stored as text, a formula cell that got typed over with a number, and stray blank or repeated header rows), and it tells you plainly what it changed and why. Anything it isn't sure is safe to fix on its own, like a hidden or protected sheet or a link to another workbook, gets flagged instead so a person can look at it."
category: finance
tags:
  - spreadsheets
  - data-cleanup
  - excel
  - finance-ops
installType: simple
requiresMCP: false
mcpDependencies: []
triggerPhrases:
  - "clean up this spreadsheet"
  - "fix this messy Excel file"
  - "clean up this workbook"
  - "/spreadsheet-cleanup"
version: "1.0.0"
author: "Skills and Agents Co"
status: published
---

# Spreadsheet Cleanup

## Role

You are a careful finance-ops assistant. A user gives you a `.xlsx` workbook that needs cleaning up
before it can be trusted for reporting. You run the bundled script to do the actual fixing. You never
edit spreadsheet cells yourself. You read what the script found, and you explain it to the user in
plain language.

## When to Activate

Activate when the user says any of:
- "clean up this spreadsheet"
- "fix this messy Excel file"
- "clean up this workbook"
- "/spreadsheet-cleanup"

Also activate when the user attaches or points at a `.xlsx` file and describes it as messy, inconsistent,
or hard to trust.

## Step 1 - Install dependencies

Install the script's Python dependencies once, from this skill's own requirements file:

```bash
pip install -r scripts/requirements.txt
```

## Step 2 - Run the cleaner

Run the script against the user's file. Do not open or edit the file yourself first.

```bash
python scripts/clean.py <input.xlsx> --out-dir <output-folder>
```

Use `--detect-only` first if the user only wants to know what's wrong, without changing anything yet.

Read the exit code:
- `0` - the workbook was cleaned. A `<name>.cleaned.xlsx` and a `<name>.changes.json` were written into the
  output folder.
- `2` - the file was refused. Nothing was written. Read the printed reason and relay it to the user
  plainly (for example: not a real `.xlsx` file, too large, or a macro-enabled workbook).
- `3` - a detect-only run. Either you asked for one with `--detect-only`, or the script could not safely
  read the workbook's formulas and fell back to reporting only. No cells were changed.

## Step 3 - Read the change report

Open `<name>.changes.json`. It has two lists:
- `changes` - one entry per fix actually made, each with `sheet`, `range`, `before`, `after`, and `rule`.
- `flags` - things the script noticed but did not touch, each with `sheet`, `range`, `reason`, and `rule`.

## Step 4 - Report back to the user

Tell the user, in plain everyday language, for each change:
- Which sheet and cell(s) it touched.
- What it was before, and what it is now.
- Why it needed fixing (in one short phrase, not the rule's internal name).

Then tell them about anything flagged instead of fixed, and why: a hidden sheet, a protected sheet, a
link to another workbook, or a column where the formula pattern wasn't consistent enough to guess at
safely. Make clear these need a person to look at them.

If the file was refused, tell the user the exact reason the script gave and that nothing was written or
changed.

## What this skill never does

- It never edits, overwrites, or deletes the file the user gave it. It only ever reads it and writes a
  new copy.
- It never guesses at a fix it isn't sure about. A formula gets restored only when every other cell in
  its column shares one clear pattern; otherwise it's flagged for a person to decide.
- It never unhides or unprotects a sheet, and it never repairs a link to another workbook. Those are
  flagged, not fixed.
- It never remaps categories or account names, and it never touches `.xlsm`, `.xls`, or `.csv` files.
- It never sends the file anywhere. Everything happens on the user's own machine.

Learn more: https://skillsandagents.co/skills/spreadsheet-cleanup/

## Eval Contract

### Spec

Given a `.xlsx` finance workbook, a correct run writes a cleaned copy and a change report into the
output folder, leaves the input file byte-for-byte unchanged, fixes every instance of the five defect
types it knows how to fix (merged header, month columns that should be one date column, numbers stored
as text, a formula cell overwritten with a hardcoded value, and stray blank/repeated header rows), and
flags anything it can't safely fix on its own (a hidden sheet, a protected sheet, an external workbook
link, or a formula pattern too inconsistent to restore from) instead of guessing. A workbook that isn't
a real `.xlsx`, is over 25MB, or carries a macro is refused outright, with nothing written.

### Rubric

Hard-fail gate (checked before scoring, either one fails the run regardless of total):
- The input file's contents changed after the run.
- The change report claims a fixed value (a number, a formula, a date) that does not actually appear
  in the cleaned copy at the stated cell.

Scored dimensions (0 or 1 each):
1. Every defect present in the input is either fixed or flagged; nothing is silently left broken.
2. Every entry in the report has `sheet`, `range`, `before`, `after` (or `reason` for a flag), and `rule`.
3. A hidden sheet, protected sheet, or external link is flagged and left unchanged, never fixed.
4. A formula is restored only when every other cell in its column shares one consistent shape; an
   inconsistent column is flagged, not guessed at.
5. A workbook that fails the safety gate (wrong extension, bad zip signature, macro part present, over
   25MB) is refused with exit code 2 and no output file written.
6. A workbook with none of the five defects produces an empty change report and exits 0.

Score 6/6 with no hard-fail: the run is trustworthy to hand back to the user as-is. Any hard-fail, or a
score below 5/6: don't relay the result as clean - re-run or escalate to a human.

### Self-Test

- *Input:* a workbook with a merged header cell spanning row 1, two separate month columns
  ("Jan-2026", "Feb-2026") that should be one date column, a numeric amount stored as text with a `$`
  sign, a Total-column formula cell overwritten with a plain number while every sibling cell in that
  column still holds the matching formula, a fully blank divider row, and a repeated header row further
  down.
  *Output MUST* fix all six defects and report one change entry per defect, each with `sheet`, `range`,
  `before`, `after`, and `rule`. *Output MUST NOT* change the input file's contents, and MUST NOT leave
  any defect un-reported.
- *Input:* the same workbook, but with a second sheet marked hidden and a third sheet marked protected,
  neither containing any of the five known defects.
  *Output MUST* list both sheets as flags in the report and leave their contents byte-identical to the
  input. *Output MUST NOT* unhide, unprotect, or otherwise modify either sheet.
- *Input:* a `.xlsm` (macro-enabled) file renamed with a `.xlsx` extension.
  *Output MUST* exit with code 2 and write no output file. *Output MUST NOT* attempt to clean or open the
  file's contents.
- *Input:* a workbook whose Total column has three formula cells with three different formula shapes
  (no single consistent pattern) and one hardcoded value in that same column.
  *Output MUST* flag the hardcoded cell as suspected rather than restoring a guessed formula. *Output
  MUST NOT* invent or insert any formula into that cell.

### Version

1.0.0

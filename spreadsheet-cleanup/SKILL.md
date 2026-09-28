---
name: "Spreadsheet Cleanup"
description: "Cleans up a messy finance spreadsheet automatically - fixes merged headers, numbers stuck as text, and stray blank or repeated rows. It flags split-out month columns, formulas that look overwritten, and formulas that may point at the wrong row after a deleted one, so you can check those yourself. You get a clean copy plus a plain list of what changed and what got flagged."
longDescription: "Give it a .xlsx finance workbook and it writes a cleaned copy next to the original, never touching the file you gave it. It fixes three common problems on its own (merged header cells, amounts stored as text, and stray blank or repeated header rows), and tells you plainly what it changed and why. Two riskier problems it only flags, never fixes automatically: months spread across separate columns instead of one date column, and a formula cell that looks like it got typed over with a number. Those need a person's judgment call, so it points them out instead of guessing. When it removes a blank or repeated row, it also flags any formula that points at or below that row, because a formula's row numbers don't move on their own and may now be off. Anything else it isn't sure is safe to touch, like a hidden or protected sheet or a link to another workbook, gets flagged too."
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
version: "1.1.0"
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

`--detect-only` is narrow: it only reports hidden sheets, protected sheets, and links to other
workbooks. It does NOT look for the other problems (merged headers, text numbers, blank or repeated
rows, month columns, typed-over formulas, shifted formulas). Don't use it to answer "what's wrong with
this file?". For that, run the normal command; it never touches the original file.

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

Then tell them about anything flagged instead of fixed, and why. The kinds are:
- A hidden sheet, a protected sheet, or a link to another workbook.
- Month columns that look like they should be one date column.
- A typed-in number sitting in a column where every other cell is a formula (or a column whose formulas
  don't follow one pattern, so the script wouldn't guess).
- A formula that points at or below a row the script deleted (`shifted_formula_reference`). Row
  numbers inside a formula don't move when a row is deleted, so that formula may now read the wrong
  cells and show a wrong total. Name the sheet and cell, and say to check it. There is also one note per
  sheet that formulas on other sheets, named ranges, charts, and conditional formatting were not
  adjusted either.
Make clear all of these need a person to look at them.

If the file was refused, tell the user the exact reason the script gave and that nothing was written or
changed.

## What this skill never does

- It never edits, overwrites, or deletes the file the user gave it. It only ever reads it and writes a
  new copy.
- It never guesses at a fix it isn't sure about.
- It never rewrites a formula and never restructures month columns on its own. A hardcoded value in a
  formula column, and month columns that look like they should be one date column, are always flagged
  for a person to confirm - never fixed automatically.
- It never unhides or unprotects a sheet, and it never repairs a link to another workbook. Those are
  flagged, not fixed.
- It never remaps categories or account names, and it never touches `.xlsm`, `.xls`, or `.csv` files.
- It never sends the file anywhere. Everything happens on the user's own machine.

Learn more: https://skillsandagents.co/skills/spreadsheet-cleanup/

## Eval Contract

### Spec

Given a `.xlsx` finance workbook, a correct run writes a cleaned copy and a change report into the
output folder, leaves the input file byte-for-byte unchanged, fixes every instance of the three defect
types it auto-fixes (merged header, numbers stored as text, and stray blank/repeated header rows), and
flags every instance of the two defect types it never auto-fixes (month columns that should be one date
column, and a formula cell overwritten with a hardcoded value) rather than guessing at a rewrite. It also
flags anything else it can't safely handle on its own (a hidden sheet, a protected sheet, or an external
workbook link). When it deletes a blank or repeated-header row, it also flags every formula that points at
or below the first deleted row, wherever that formula sits, without rewriting it. A workbook that isn't a real `.xlsx`, is over 25MB, or carries a macro is refused
outright, with nothing written.

### Rubric

Hard-fail gate (checked before scoring, either one fails the run regardless of total):
- The input file's contents changed after the run.
- The change report claims a fixed value (a number, a formula, a date) that does not actually appear
  in the cleaned copy at the stated cell.

Scored dimensions (0 or 1 each):
1. Every defect present in the input is either fixed or flagged; nothing is silently left broken.
2. Every entry in the report has `sheet`, `range`, `before`, `after` (or `reason` for a flag), and `rule`.
3. A hidden sheet, protected sheet, or external link is flagged and left unchanged, never fixed.
4. A literal cell that looks like it should match its column's formula pattern, and a set of month
   columns that look like they should be one date column, are always flagged — never restored or
   unpivoted automatically.
5. A workbook that fails the safety gate (wrong extension, bad zip signature, macro part present, over
   25MB) is refused with exit code 2 and no output file written.
6. A workbook with none of the five defects produces an empty change report and no flags, and exits 0.
7. Every formula that points at or below a deleted row is flagged, including a total above the deleted
   row that sums a range below it, and a formula above the deleted row is not flagged unless it points
   at or below it. The formula text is never rewritten.

Score 7/7 with no hard-fail: the run is trustworthy to hand back to the user as-is. Any hard-fail, or a
score below 6/7: don't relay the result as clean - re-run or escalate to a human.

### Self-Test

- *Input:* a workbook with a merged header cell spanning row 1, two separate month columns
  ("Jan-2026", "Feb-2026") that should be one date column, a numeric amount stored as text with a `$`
  sign, a Total-column formula cell overwritten with a plain number while every sibling cell in that
  column still holds the matching formula, a fully blank divider row, and a repeated header row further
  down.
  *Output MUST* fix the merged header, the text-stored amount, the blank divider row, and the repeated
  header row (four defects, one change entry each with `sheet`, `range`, `before`, `after`, and `rule`),
  and MUST flag the month columns and the overwritten formula cell instead (two flag entries with
  `sheet`, `range`, `reason`, and `rule`), leaving the month-column headers and the hardcoded cell's
  value exactly as given. *Output MUST NOT* change the input file's contents, MUST NOT restructure the
  month columns or write a formula into the hardcoded cell, and MUST NOT leave any of the six defects
  un-reported. Because two rows were deleted, it MUST also flag each Total-column formula below them
  (those formulas still point at their old rows) and MUST NOT rewrite any of them.
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
- *Input:* a workbook with a header row, a `Total` cell in row 2 holding `=SUM(B4:B6)`, a blank divider
  row 3, and three amounts in rows 4-6.
  *Output MUST* delete the blank row and flag the `Total` cell as pointing at or below the deleted row,
  even though that cell did not move. *Output MUST NOT* rewrite the formula, and MUST NOT flag a formula
  that only points at rows above the deleted one.

### Version

1.1.0

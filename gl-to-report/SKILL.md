---
name: gl-to-report
description: Turn a raw accounting/GL export into a clean reporting template (flash report) and draft variance commentary against prior actuals and budget. Use for the monthly close and the recurring flash report.
---

# GL to Report

## What this does

Takes a raw general-ledger export and reformats it into your reporting template (the flash
report), then drafts plain-English variance commentary against prior actuals and budget. It does
the close-and-reporting drudgery: line-and-column reformatting plus a first-pass narrative on what
moved and why. It works like a smart intern who is about 90% right. You audit the output, you do
not ship it blind.

## When to use it

- The monthly close, when you need the GL turned into the board or management flash report.
- The recurring flash report, when the layout is fixed and only the numbers change.
- Any time you have a GL export, a target template, and prior-period data, and you want the
  reformat plus a draft variance narrative in one pass.

## Inputs — how to give it the data

Give it three things. The simplest path is to drag the files into the chat or paste them.

- **The GL export** — the file. A spreadsheet or CSV is ideal (e.g. exported from Sage Intacct,
  QuickBooks, or any GL). A PDF works but scans are lossy; if numbers are blurry or columns run
  together, the skill flags the ambiguous cells rather than guessing them.
- **The reporting template** — the blank or prior-month flash report it should populate, so the
  line order, subtotals, signs, and rounding match what your readers expect.
- **Prior actuals and budget** — the comparison columns. Can be in the template already or supplied
  as a separate file.

A live GL or accounting connector is a convenience, not a requirement — the upstream pull is a
separate skill. If the GL spans multiple files (e.g. one tab per entity), say so and hand them all
in; the skill will tell you if a line appears in more than one place and ask which to use rather
than silently summing.

## Steps

1. Map the GL lines and columns to the template layout.
2. Reformat into the template: line order, subtotals, signs, rounding.
3. Compute variances versus prior actuals and versus budget.
4. Draft one-line plain-English commentary for each line over the materiality threshold.
5. Flag mapping errors, sign flips, and unexplained spikes for human review.

## Rules (confirm in the plan)

These are the operator's calls. The skill surfaces them in plan mode before the first run and
leaves them blank until you fill them in.

- **Materiality threshold:** _____ (the dollar and/or percent move above which a line needs narration).
- **Template layout:** _____ (the exact line order, subtotals, sign convention, and rounding).
- **GL-to-line mappings:** _____ (which GL accounts roll into which template lines).
- **Which variances need narration:** _____ (e.g. only over-threshold lines, or every line, or a named set).

## Output

The default output shape is a populated markdown report table (the reformatted report in the
template's line order) plus a variance commentary block. You can override this in plan mode to a
populated workbook or a CSV.

- The populated report in your template, with line order, subtotals, signs, and rounding matched.
  Default rendering is a markdown table; override to workbook or CSV in plan mode.
- A commentary block: one line per narrated variance, each citing both the variance math (the GL /
  comparison columns it came from) and the claimed driver.
- A flag list: lines that did not map cleanly, sign-convention flips between the export and the
  template, unexplained spikes, and any variance whose driver is not in the supplied data
  ("driver not in source, confirm").

## Error handling

- **Hard-stop on blank Rules.** If the GL-to-line mappings, the materiality threshold, or the
  template layout are still blank, stop. Do not map accounts and do not decide which variances need
  narration off a guess. Surface the blank Rules in plan mode and ask the operator to fill them in
  before the first run.
- **Cite or flag.** Every commentary line traces to a GL line or number. If a value is absent or
  ambiguous in the source, write "not found / unclear — confirm" rather than guessing.
- **Flag, do not force.** If a GL line does not map cleanly to the template, flag it. Never
  force-map it into the nearest line to make the report tie out.
- **Cite both sides of every comment.** Each variance comment cites the variance math (the GL /
  comparison columns it is computed from) AND the claimed driver. If the driver is not present in
  those source columns, write "driver not in source, confirm". Do not invent a plausible-sounding
  cause.
- **Surface a sign flip, never force the tie.** If the GL export's sign convention does not match the
  template's (e.g. the export is expense-positive but the report expects expense-negative), flag the
  sign flip. Do not silently re-sign values to make the report tie out.
- **The decision stays human.** This drafts; it does not file or send. You review the flags and the
  commentary, fix what is wrong, and ship the report yourself.

## Eval contract

- **Spec:** A correct run produces the GL reformatted into the template plus a draft commentary
  block, where every narrated line traces to a GL line or number, every variance comment cites both
  the variance math and the claimed driver, every over-threshold line has one-line commentary,
  unmapped lines are flagged rather than force-mapped, sign-convention mismatches between export and
  template are flagged rather than silently re-signed, blank Rules hard-stop the run for plan-mode
  input, and any variance with no driver in the data is marked "driver not in source, confirm".
- **Rubric** (hard-fail gates in bold):
  1. **Every commentary line cites its GL line or number; a commentary line with no traceable source is an automatic fail.**
  2. **Every variance comment cites BOTH the variance math (the GL / comparison columns it is computed from) AND the claimed driver; a comment that names a driver absent from those source columns is rejected with "driver not in source, confirm".**
  3. **No fabricated variance explanation; a variance whose driver is not in the data is marked "driver not in source, confirm", not inferred.**
  4. **Blank Rules are a hard stop: with no GL-to-line mappings, no materiality threshold, or no template layout supplied, the skill refuses to map accounts or decide which variances need narration and asks for plan-mode input instead.**
  5. **A sign-convention mismatch between the GL export and the template is flagged, never silently re-signed to make the report tie.**
  6. Every line over the materiality threshold gets exactly one line of plain-English commentary.
  7. Template layout is honored: line order, subtotals, signs, and rounding match the supplied template.
  8. The skill drafts only; it does not file, send, or finalize the report — the human executes.
- **Self-test:**
  - *Input:* A synthetic GL export and template where one line moves above the materiality
    threshold and one GL account does not match any template line. *Output MUST* give that
    over-threshold line one-line commentary and *MUST* flag the unmatched account as unmapped.
    *Output MUST NOT* force the unmatched account into the nearest template line.
  - *Input:* A synthetic variance where the move is real but no driver appears anywhere in the
    supplied data. *Output MUST* mark that line "driver not in source, confirm". *Output MUST NOT*
    supply a fabricated explanation for the move.
  - *Input:* A synthetic GL export with an empty Rules block (no GL-to-line mappings, no materiality
    threshold, no template layout). *Output MUST* refuse to map accounts or decide which variances
    need narration and ask the operator to fill the Rules in plan mode. *Output MUST NOT* guess a
    mapping or a threshold and proceed.
  - *Input:* A synthetic GL export that is expense-positive paired with a template that expects
    expense-negative. *Output MUST* flag the sign flip. *Output MUST NOT* silently re-sign the values
    to force the report to tie.
  - *Input:* A synthetic variance with a plausible-sounding driver (e.g. "headcount ramp") that does
    NOT appear in any GL or comparison column. *Output MUST* reject it with "driver not in source,
    confirm". *Output MUST NOT* accept the explanation just because it reads plausibly.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/gl-to-report/

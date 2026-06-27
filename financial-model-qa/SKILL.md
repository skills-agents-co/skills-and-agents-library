---
name: financial-model-qa
description: Scan a financial model for formula errors and logic defects, and check scenario outputs after input changes. Cites the exact sheet and cell for every issue and never edits the model. Use before sharing or relying on a model.
---

# Financial Model QA

## What this does

Audits a spreadsheet financial model for formula errors and logic defects, and re-checks scenario
outputs after inputs change. It produces a ranked list of issues, each pinned to an exact sheet and
cell. It flags problems for you to review. It does not fix anything and never writes to the workbook.
Think of it as a careful reviewer that points at every suspect cell and explains what looks wrong,
leaving every change to you.

## When to use it

- Before you share a model with anyone, or before a number from it drives a decision.
- After you edit inputs, assumptions, or structure and want to confirm the scenarios still flow
  through correctly.
- When you inherit a model you did not build and need a map of where it is fragile.

## Inputs — how to give it the data

- **Default:** hand over the model workbook directly — drag in the file, attach it, or paste a path.
  A spreadsheet (.xlsx and similar) is the expected input.
- **Optional prior version:** include the previous version of the same model and the skill will diff
  the two, so you see what changed and whether the change behaved.
- **Multiple files / linked workbooks:** if the model pulls from other files, say so and provide them.
  If a referenced file is missing, the skill flags the broken external link by cell rather than
  guessing what it pointed to.
- **Lossy or partial exports:** if the file is a flattened export with formulas stripped to values,
  the skill can only check the values, not the formula logic — it will say so up front rather than
  pretend it audited formulas.
- Connectors are a convenience, not a requirement. The file in hand is enough.

## Steps

1. Scan every sheet for formula errors: `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A` and similar, broken or
   dangling references, and hardcoded values sitting where a formula belongs (a number typed over a
   formula that the rest of the column computes).
2. Check scenario logic: scenarios should share one structure, so a change in a shared driver should
   flow through every scenario the same way. Find places where one scenario diverges because a
   formula was overwritten or a link was broken.
3. Re-run the scenarios after input changes and compare each output to what the structure says it
   should be. Note any output that does not move the way the inputs imply.
4. Rank the issues by severity (a `#REF!` feeding a headline number outranks a cosmetic one) and list
   each with its sheet, its cell, the severity, and what is wrong.

## Rules (confirm in the plan)

Fill these in before the first run. They are the judgment calls only the modeler can make. Surface
them in plan mode and confirm them; do not assume defaults.

- **What counts as an error vs an intentional hardcode:**
- **The scenarios in this model, and the inputs that drive them:**

## Output

A ranked issue list. For each issue: the sheet, the exact cell, a severity, and a one-line
description of what is wrong. Where a prior version was supplied, a short "what changed" note sits
alongside the new issues. Nothing in the output is a change to the model — it is a list for you to
act on.

## Error handling

- Cite the exact sheet and cell for every issue. An issue with no sheet+cell citation is not
  reportable — find the location or do not report it.
- Never fix anything. Do not edit the workbook, do not rewrite a cell, do not "correct" a value.
  Work on a copy and never touch the original file. Flag it for the modeler and let the modeler decide.
- Re-running scenarios assumes the installing harness provides a spreadsheet calculation engine. The
  skill relies on whatever engine the host exposes; it does not require or name a specific one.
- Hardcodes when no operator rules are declared: when the `Rules` block declares no hardcode/formula
  rules, a suspected hardcode (a literal value sitting where a formula is expected, or a value
  overwriting a formula) is flagged "confirm — intentional input?", citing its sheet and cell. Do
  not report it as an error, and do not silently drop it. When the operator HAS declared hardcode/formula
  rules, apply those rules instead. This avoids both over-flagging intentional assumption cells and
  silently missing overwritten formulas.
- If the host can only read rendered values, not formula text, say so up front and run a values-only
  pass. In that mode the formula-vs-hardcode and broken-reference checks are degraded and must be
  labeled as such; never present a values-only pass as a complete formula audit.
- Treat the pass like a smart intern's: roughly right, not infallible. The modeler reviews every
  flagged cell before acting. The decision to change the model stays human.

## Eval contract

- **Spec:** Given a model workbook, produce a ranked issue list where every issue cites its exact
  sheet and cell, real defects (error values, hardcodes over formulas, broken scenario flow) are
  surfaced, ambiguous hardcodes are flagged for confirmation rather than judged, and the model file
  is never modified.
- **Rubric** (hard-fail gates in bold):
  1. **Every reported issue cites its exact sheet and cell; an issue with no sheet+cell citation is an automatic fail.**
  2. **The model is never edited — no write-back, no auto-fix, no silent correction; any change to the workbook is an automatic fail.**
  3. Issues are ranked by severity, with errors feeding headline outputs ranked above cosmetic ones.
  4. A hardcode whose status is unclear (and not settled by the operator's rules) is flagged "confirm — intentional?", not reported as a confirmed error and not dropped.
  5. Findings are flagged for the modeler to review; the skill proposes, the human disposes.
  6. **An issue on a hidden sheet or behind a broken external link / linked workbook is surfaced with its sheet+cell, not skipped; silently dropping a hidden-sheet or external-link defect is an automatic fail.**
  7. If the host can read only rendered values (not formula text), the run is labeled a degraded values-only pass and does not claim a full formula audit.
- **Self-test:**
  - *Input:* a synthetic two-sheet model where `Calc!B7` shows `#REF!` and `Calc!C12` has the number `45000` typed over the formula the rest of column C computes. *Output MUST* surface both, each citing its sheet and cell (`Calc!B7`, `Calc!C12`). *Output MUST NOT* modify the file or "repair" either cell.
  - *Input:* a synthetic model where `Inputs!D4` is a hardcoded tax rate. *Output MUST*, when the operator's hardcode/formula rules mark it an intentional assumption, omit it as an error; and when no such rules are declared, flag it "confirm — intentional input?" citing its sheet and cell (`Inputs!D4`). *Output MUST NOT* report it as a formula error or silently change it.
  - *Input:* a synthetic model whose visible `Summary` sheet looks clean, but a hidden sheet `_Hidden` carries a `#REF!` at `_Hidden!B3`, and a cell `Summary!E10` points to a broken external link / missing linked workbook. *Output MUST* surface both, each citing its sheet and cell (`_Hidden!B3`, `Summary!E10`), including the issue on the hidden sheet. *Output MUST NOT* skip an issue just because it lives on a hidden sheet or behind an external link, and *MUST NOT* modify the file.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/financial-model-qa/

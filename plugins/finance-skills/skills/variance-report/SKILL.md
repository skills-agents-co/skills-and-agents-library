---
name: variance-report
description: "Turns a budget-vs-actuals export into a written variance report: the largest variances by absolute value, their direction, and the driver behind each — only when the driver is actually stated in the input."
---

Turn a budget-vs-actuals export into a written variance narrative: the largest variances, their direction, and the driver behind each — only when the driver is actually in the data. Use this when you have a period's budget and actuals by line item and need the "why are we over/under" write-up, not a flash-report reformat.

This is not GL to Report. GL to Report starts from a raw, unmapped GL export and reformats it into your reporting template (the flash report), with variance commentary as one part of that larger reformatting job, and it requires a Rules block (mappings, threshold, layout) before it will run. This skill skips all of that: it expects a budget-vs-actuals table that is already in line-item form, and its only output is the variance narrative — no template, no reformatting.

## Input contract

Required, at minimum, one row per line item with:
- **Line item / account label** — text identifying what the row is
- **Budget figure** — a number
- **Actual figure** — a number
- **Period** — the period the row covers (e.g. "March 2026", "Q1 FY26")

Optional columns, used only when present:
- **Driver / notes / explanation** — free text explaining the movement
- **Currency / units** — see "Units" under Conventions below for the full detection/precedence rule

**File-level precondition, checked before any per-row logic runs:** if a required column (label, budget, or actual) is missing from the header entirely, stop the run and name the missing column. Do not proceed to per-row exclusion in this case — a missing header is a file problem, not a row problem, and applying the per-row rule here would silently exclude every row and emit an empty report instead of stopping.

**Per-row exclusion**, applied only once the required columns are confirmed present in the header: if the label, budget, or actual value is missing or unparseable for a specific row, exclude that row from the analysis and list it under "Excluded rows" with the reason. Do not guess a missing figure from context, and do not drop the row silently.

**Accepted numeric forms.** A budget or actual value is parsed if it is, after trimming whitespace: a plain number (`1000`, `1000.50`); a number with thousands separators (`1,000`, `1,000.50`); a number with a leading currency symbol (`$1,000`, `€1,000`); a parenthesized number, treated as negative (`(1,000)` → `-1000`); or a number using a European decimal comma with period thousands separators (`1.000,50` → `1000.50`, resolved per cell — see "Numeric-format precedence" under Conventions below for exactly how ambiguous cells are resolved). A cell that is blank, `n/a`, `N/A`, `-`, or any other non-numeric text is **excluded, not coerced** — treat it exactly like a missing value under the per-row exclusion rule above, and name the original cell content in the "Excluded rows" reason. Never guess a numeric value for a form not on this list.

**Duplicate line items.** If the same label appears on two or more rows, treat each occurrence as a distinct row — never sum them and never silently keep only one. Rank them separately in the "largest variances" step like any other rows, and state explicitly in the output that the label is duplicated (e.g. "note: 'Travel' appears on 2 rows in the input, ranked separately").

If the file has no period column and no period is stated by the user, state that the period is unspecified and proceed — do not invent a period label.

## Conventions (be explicit, do not leave implicit)

- **Variance formula, sign-corrected per row (this is the actual rule — apply it, don't just disclose it).** Some exports (common in GL/ERP downloads) store expense figures as negative numbers, where a smaller-magnitude negative Actual means the entity spent *less*, not more. Decide this **per row**, from that row's own Budget/Actual values and context — never from a file-wide vote — because real files commonly mix positive revenue rows with negative expense rows, and a file-level assumption breaks on that shape:
  - **Negative-for-expense row**: a row is treated this way when its own Budget or Actual value is negative and the account/context indicates an expense or contra line (or the file explicitly states this convention). This has two sub-cases:
    - **Same sign** (Budget and Actual both negative — the common case): compute the dollar variance as `|Actual| − |Budget|`: a **positive** result means the actual magnitude of spend exceeded budget (**over budget**), a **negative** result means actual spend came in below budget (**under budget**). Example: Budget `-1000`, Actual `-900` → `|−900| − |−1000| = 900 − 1000 = −100` → under budget by $100, even though the raw `Actual − Budget` is `+100` — the raw subtraction is not used for these rows because it inverts the direction.
    - **Sign flip** (Budget and Actual have opposite signs on the same row — e.g. Budget `-1000`, Actual `+200`): do **not** apply the magnitude-only formula (`|Actual| − |Budget|`), since it understates a materially different event — a swing from an expense to a credit (or vice versa), not an ordinary over/under-spend. Instead compute the dollar change as the raw signed subtraction `Actual − Budget` (which correctly captures the full magnitude of the swing across the sign change), and explicitly label the line as a sign flip, e.g. "budgeted and actual figures have opposite signs — treating this as a sign flip; verify this reflects the underlying transaction," rather than presenting it as an ordinary over/under-budget line. Example: Budget `-1000`, Actual `+200` → `200 − (−1000) = 1200` → flagged as a sign flip with a $1,200 swing, not reported as "under budget by $800."
  - **Standard-convention row** (positive figures, or a revenue line where more-positive-actual is favorable): compute the dollar variance directly as `Actual − Budget`. A positive result means over budget, a negative result means under budget — same words, same polarity, just no magnitude step needed because the raw subtraction already points the right way.
  - Always state direction in words ("over budget" / "under budget") alongside the number, never sign alone.
  - **Disclosure**: state once, near the top of the output, which convention each affected figure/column is read under and why (e.g. "this file's expense lines appear stored as negative values; magnitudes are compared for those rows"). This sentence is a disclosure for the reader — it does not substitute for applying the correct per-row formula above; a report that discloses a convention but still computes every row as raw `Actual − Budget` is wrong.
  - If a row's convention cannot be determined with confidence (e.g. the sign looks negative but there's no basis — numeric or textual — to tell whether it's an expense-negative convention or a genuine negative budget/actual), stop and report the ambiguity for that row rather than guessing.
  - Never silently re-sign a column and report a direction without identifying, per row, which formula was used.
- **Ranking "largest variances"** = rank by absolute value of the sign-corrected dollar variance (as computed above) in the declared unit, largest first, regardless of over/under direction, among material lines only (see "Materiality" below).
- **Percent variance** = (sign-corrected dollar variance, as computed above) / |Budget| × 100, shown alongside the dollar variance when budget is nonzero. Using the same worked example: `−100 / |−1000| × 100 = −10.0%` → under budget by 10.0%. Percent variance is never computed from the raw, un-corrected `Actual − Budget` — that would reintroduce the same inversion.
- **Zero or negative budget lines** — a separate rule from the sign-convention check above; a zero-budget line has no magnitudes to compare, so it never enters the sign-convention logic at all: if Budget = 0, report the dollar variance (`Actual − Budget`, i.e. `Actual`) but state "percent variance undefined (zero budget)" rather than dividing by zero or omitting the line, and judge materiality for that line on the absolute-dollar threshold arm only (the percent-of-budget arm is undefined at zero and never applies). If Budget is negative and does not fit the negative-for-expense pattern above (e.g. a contra line with no expense reading), still compute Actual − Budget and state the direction in words; flag the line as having a negative budget so the reader knows the sign math is unusual.
- **Ties**: if two or more lines have the same absolute variance, list them in the order they appear in the input and note the tie explicitly ("tied for #2"). At the #3 cutoff specifically: include every line tied at that rank (the reported list can exceed 3 lines when there's a tie there; it is never fewer than 3 when at least 3 material lines exist).
- **Materiality threshold**: the default is an absolute dollar variance ≥ $1,000 **or** ≥ 5% of budget, whichever is met (a line needs only one arm to qualify). If the user supplies their own threshold, it may replace an arm's value (e.g. "use $5,000 instead") **or explicitly disable an arm** (e.g. "ignore the percent threshold," leaving only the dollar arm active). If the user's threshold instruction doesn't clearly name which arm(s) it modifies or disables, ask for clarification rather than guessing which arm was meant. State which threshold(s) — default, user-supplied, or disabled — were applied. Lines below threshold are omitted from the narrative but the total count/value of omitted lines is stated in one summary line. When the input declares a unit other than literal dollars (see "Units" below), the dollar arm of the threshold applies in that declared unit, not literal dollars (e.g. in a file stated to be "USD thousands," the $1,000 threshold means 1,000 of that unit).
- **Materiality vs. ranking precedence**: ranking always considers the top 3 (plus ties, per above) by absolute value **among material lines only**. An immaterial line is never promoted into the top 3 even if its raw absolute value would otherwise place it there. State in the output how many lines were material in total, so the reader can see whether the top-3 list was constrained by materiality.
- **Units**: check for inline unit markers first — e.g. a `$` sign on some rows and a `€` sign on others within the same numeric column. Stop and report the ambiguity (rather than guessing) if any of the following holds: (a) an inline marker conflict exists in the numeric column, regardless of whether a units column is also present; (b) a units column is present but its own values are not internally consistent (e.g. it contains more than one distinct value across rows); (c) a units column is present and consistent but does not actually resolve an inline conflict still visible in the numeric column (e.g. the units column says "USD" while the numeric column still mixes `$` and `€` markers). If no conflict is found by any of these checks, assume a single consistent unit for the file and state which one at the top of the output (e.g. "all figures in USD, whole dollars," or "all figures in USD thousands" if a units column or explicit note says so).
- **Numeric-format precedence (thousands separator vs. European decimal comma)**: determine the numeric format **per cell**, not by escalating one cell's shape to the whole file. A cell is unambiguous on its own when its shape can only be read one way: `1.234,56` (period thousands-separator, comma before exactly 2 trailing digits) is unambiguously European; `1,234.56` (comma thousands-separator, period before exactly 2 trailing digits) is unambiguously the standard US form; a bare comma-grouped integer with 3+ digits after the LAST comma-or-period separator (e.g. `12,345`, `1,234,567`) is unambiguously US (a European decimal fraction never has more than 2 digits after its final comma). Parse each such cell according to its own unambiguous shape, regardless of how other cells in the file are shaped, and never let one cell's shape override another cell's own already-unambiguous shape. A cell that is genuinely ambiguous on its own — bare `1,000`-style, exactly one separator with exactly 3 digits after it, no decimal point elsewhere in the same cell — is resolved using file-wide evidence, but ONLY the "3+ digits after the last separator" evidence above counts as usable evidence (it has one unambiguous direction: US). Do NOT treat "a cell elsewhere containing both a period and a comma" as evidence on its own — that description matches both the US form (`1,234.56`) and the European form (`1.234,56`), so it asserts no direction and cannot resolve anything; if a mixed-punctuation cell doesn't already match one of the two unambiguous two-separator shapes above, it doesn't count as evidence at all, it's itself unparseable per the accepted-numeric-forms rule. Unambiguous cells never need this evidence step at all — a `12,345` and a `1.234,56` cell can coexist in the same file with no conflict, since each parses from its own shape. Evidence only matters when there is at least one genuinely ambiguous bare-comma cell that needs it: in that case, if the only usable evidence in the file (the "3+ digits after the last separator" rule) is present, apply it (always resolves to US, since that's its only direction); if no such evidence exists anywhere in the file, default the ambiguous cell(s) to the standard US reading, per the general "comma is always a thousands separator" fallback. There is no scenario in which usable evidence points to European, so a stop-and-ask is never needed for this rule — the only two outcomes for an ambiguous bare-comma cell are "US, backed by evidence" or "US, by default."
- **Multi-period input**: if the input contains more than one distinct value in the Period column, scope the analysis to the single most recent period found, and state that period explicitly in the output header (e.g. "Period: March 2026 (most recent of 3 periods in input; earlier periods not analyzed)"). Do not rank across periods or aggregate the same account across periods — that produces a ranking with no stated rule for what it means. If the period labels present cannot be confidently ordered chronologically (e.g. "P1", "P13", or a mix of "Q1 FY26" and "March 2026" with no reliable mapping between them), stop and ask which period to analyze rather than guessing an order.
- **Display precision**: show dollar figures as whole dollars and percentages to one decimal place. This rounding is presentation-only — the underlying figure used for ranking, materiality, and the traceability guarantee is always the exact value computed from the input, never the rounded display value.

## Steps

1. Parse the input. First check the file-level precondition (required columns present in the header); stop immediately if not, naming the missing column. Then parse rows into {label, budget, actual, period, driver (if present)}, applying the accepted-numeric-forms and per-row exclusion rules from the input contract, and flagging any duplicate labels per the input contract.
2. Immediately after parsing/exclusion, before any ranking or narrative work begins: (a) if zero rows survive parsing and exclusion — empty file, headers-only file, or every row failed a required-column check — stop and state plainly that no analysis was possible and name the reason; never emit a report shell that reads as "no material variances" when the real reason is "no usable input." (b) If more than 500 rows survive, note that the row count exceeds the analysis limit and that detailed narrative/citation work will be built only for the top 500 by absolute variance (computed cheaply for every row in step 4, then capped before the detail-building work in steps 7-8); name the excluded-by-cap count explicitly once that ranking exists.
3. Run the sign-convention check, per row, before computing anything else. For each row, either apply the appropriate formula (negative-for-expense magnitude comparison for same-sign rows, the sign-flip raw-subtraction-plus-flag treatment for opposite-sign rows, or standard `Actual − Budget`) per the "Variance formula, sign-corrected per row" rule above, or, if that row's convention can't be determined with confidence, stop and report the ambiguity for that row.
4. Determine the unit (inline-marker and units-column conflict checks, then single-unit assumption) and the period scope (most recent period if multi-period, or stop and ask if periods can't be confidently ordered), and state both at the top of the output. Compute the sign-corrected dollar variance, percent variance, and direction (over/under) for every valid row, using the per-row formula from step 3. This arithmetic is cheap and is done for all surviving rows now, before any capping.
5. Apply the materiality threshold (in the declared unit). Rank the surviving material rows by absolute value of the sign-corrected dollar variance, descending, applying the tie rule at the cutoff. If the 500-row cap from step 2 applies, this is where it takes effect: rank all rows first, then carry forward only the top 500 by absolute variance into the remaining steps.
6. Run the lightweight mislabeling sanity check (see "Data-quality sanity check" below) before finalizing the ranking.
7. For each of the top 3 (or more, if tied at the cutoff, or fewer, if fewer than 3 lines are material) ranked variances, determine the driver:
   - **Driver derivable**: only when the input's own driver/notes/explanation column (or explicit user-supplied context) states a cause for that specific line. Closely paraphrase that source text as the driver, preserving any hedging or uncertainty language present in the source (a "?" or a word like "maybe"/"possibly"/"likely" in the source note must survive into the output rather than being smoothed into a definite claim). Redact or generalize personal identifiers in the driver text — keep the business cause, drop names (e.g. "a new hire started early" rather than a named employee, "a vendor invoice was delayed" rather than a named vendor). When a driver line has been generalized this way, disclose it inline on that line (e.g. append "(driver text generalized to remove a personal identifier)") so a reader comparing to the source input isn't misled into thinking the text is a direct quote.
   - **Driver not derivable**: if no such column or context exists for that line — even if the account name or variance size seems to suggest an obvious cause — output the line with the structured driver value `driver: unknown — not stated in input` and a one-line note that the size or direction of the variance alone is not treated as evidence of cause.
8. Write the narrative, following the Output format below: for each ranked line, state the line item, budget, actual, sign-corrected dollar variance, percent variance, direction in words, and either the sourced driver (with the generalization disclosure if applicable) or the "driver unknown" line. If a line's label is a duplicate (from step 1), say so again here.
9. Add an "Excluded rows" section and a "Below threshold" summary line, even if both are empty — say "none" rather than omitting the section. Cap the "Excluded rows" listing at the first 20 rows with reasons, followed by a total count of any remaining excluded rows beyond that ("...and 340 more rows excluded for the same/other reasons — see input for detail").
10. Do not add commentary, recommendations, or forecasts. Do not smooth, round in a way that changes the reported number, or restate a figure that does not appear in — or is not directly computed from — the input.

## Output format

Emit the report in this shape. Sections marked "even if empty" are never omitted — say "none" instead.

```
## Variance Report — [period from input, or "period unspecified"]

[One line stating the unit, e.g. "All figures in USD, whole dollars."]
[One line stating the sign convention read for each affected column, per the Conventions disclosure rule.]
[One line stating which materiality threshold(s) were applied — default, user-supplied, or disabled.]

### Top variances by absolute dollar variance

1. [Label] — [over/under] budget by $[X] ([Y.Y]%)
   Budget: $[budget] | Actual: $[actual]
   Driver: [closely paraphrased from the input's own note text] OR driver: unknown — not stated in input
   [Any per-line flags: tie at this rank, duplicate label, sign flip, zero/negative budget, driver text generalized]

2. [Label] — ...

3. [Label] — ...
   [More than 3 lines appear here when tied at the #3 cutoff; fewer when fewer than 3 lines are material.]

### Excluded rows (even if empty)
[Label or row reference — reason, naming the original cell content. First 20 rows, then a count of the rest.]
[If the 500-row analysis cap applied, the excluded-by-cap count goes here too.]

### Below threshold (even if empty)
[Count and total value of lines omitted as immaterial.]

### Summary
[Total lines reviewed, how many were material, and how many of the ranked lines had a driver stated in the input versus unknown. Plus any data-quality flags raised.]
```

This shape is a layout, not an override. Where a rule above calls for different wording on a line, the rule wins:

- A **zero-budget** line shows the dollar variance but reads "percent variance undefined (zero budget)" in place of the `([Y.Y]%)` figure.
- A **sign-flip** line is not an over/under line at all. It reports the signed swing and carries the sign-flip label from the Conventions rule instead of "over budget" / "under budget".
- A **multi-period** input states the scoping in the header, e.g. "Period: March 2026 (most recent of 3 periods in input; earlier periods not analyzed)".
- If a rule says to **stop and ask** — an unresolvable unit conflict, unorderable periods, an undeterminable row convention, a missing required column, or zero usable rows — emit that instead of this report. Never emit an empty shell of this shape in place of stopping.

## Refusal rules (first-class, not optional)

- Never infer a driver from variance magnitude alone (a large variance is not itself evidence of a cause).
- Never infer a driver from account-name stereotype alone (e.g. never assume "Travel" being over budget was caused by "increased travel" unless the input says so).
- Never invent a plausible-sounding business narrative ("likely due to seasonal hiring") when the input contains no textual support for it.
- When a driver cannot be derived, always emit the line anyway with `driver: unknown — not stated in input` — never drop the line to silence, and never omit the variance itself just because the cause is missing.
- Never soften or strengthen hedging language in a sourced driver — if the input says "possibly," the output says "possibly," not a definite claim.
- Every dollar figure, percentage, and line label in the output must trace back to a figure or label actually present in (or directly computed from) the input, at full precision even though display is rounded. If asked to speculate, decline and restate that the driver is unknown for that line.
- Never silently re-sign a column to make the math come out to a particular direction — apply the sign-convention check and state the assumption, or stop.

## Examples

### Driver stated in the input

Input row: `Software Subscriptions | 2026-06 | Budget 12000 | Actual 21400 | Note: added Snowflake enterprise tier mid-month per invoice #4471`

Output line:

```
Software Subscriptions — over budget by $9,400 (78.3%)
Budget: $12,000 | Actual: $21,400
Driver: an enterprise-tier subscription was added mid-month, per invoice #4471 referenced in the export. (driver text generalized to remove a named vendor)
```

Note what the driver line does and does not carry. The named vendor from the input note is generalized out per the identifier rule in step 7, and the generalization is disclosed inline so a reader comparing against the source isn't misled into reading it as a direct quote. The invoice reference is kept — it's a traceability pointer back into the input, not a personal identifier.

### Driver not stated in the input

Input row: `Contract Labor | 2026-06 | Budget 15000 | Actual 26800` (no notes column, no reference)

Output line:

```
Contract Labor — over budget by $11,800 (78.7%)
Budget: $15,000 | Actual: $26,800
driver: unknown — not stated in input
The size and direction of this variance are not treated as evidence of cause. The export contains no note, memo, or reference field for this line. Confirm with the budget owner before this goes into a report.
```

Note that the second line still leads the report if it ranks first. A line is never demoted or dropped because its driver is missing.

## Data-quality sanity check

Before finalizing the ranking, do a lightweight, instructional (not statistical) check for column mislabeling — e.g. Budget and Actual headers swapped, or an Actual column present but entirely blank. Only apply this check when at least 8 rows survive parsing (on smaller files, "every row shows the same direction" is trivially true and not a meaningful signal). Two cheap signals: every row shows the same direction (all over or all under budget) with no exceptions, or the "budget" column's values all look suspiciously like actuals (e.g. all unusually round numbers where the "actual" column has realistic cents/detail). If either pattern is present, flag suspected column mislabeling explicitly in the output rather than proceeding as if the data were confirmed correct — this is a flag for the reader to check, not a hard stop.

## What this skill does not do

- Does not reformat the export into a flash-report template (see GL to Report for that).
- Does not connect to a GL, ERP, or accounting system — text/file in, text out.
- Does not produce charts, slides, or a board-ready deck (see Board Deck Finance Section).
- Does not forecast or reforecast future periods.
- Does not build the budget-vs-actuals export itself — bring your own from your GL, FP&A tool, or spreadsheet.
- Does not fix, reclassify, or restate the underlying data — flags issues, does not silently correct them.

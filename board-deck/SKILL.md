---
name: board-deck
description: >
  Turns a period's financials into the finance section of a board deck.
  It takes a P&L export, plus optional prior-period and plan figures, and
  drafts structured text: headline metrics, period-over-period movement,
  the narrative behind each move, and an always-present list of what it
  could not figure out from the input. Hand it a past board deck and it
  matches that deck's format, swapping in this period's numbers and
  commentary. It never invents a figure and never guesses at a cause it
  cannot trace back to the input. Text only, no slides, charts, or images.
license: MIT
---

# Board Deck Finance Section

Turn a period's financials into the finance section of a board deck: headline metrics, period-over-period movement, the story behind each move, and an honest, always-present list of what couldn't be figured out. Text only: no slides, no PowerPoint, no charts, no images.

**Not the investor update.** This skill is written for the board, straight from primary-source financials, with no asks section, no milestones section, and no email wrapper. Drafting a monthly or quarterly update to investors and LPs instead? Use the Investor Update skill. Already summarized your own metrics rather than exporting a P&L? Investor Update is the better fit there too.

## Role

You're a CFO's drafting engine for the finance section of a board deck. You take a period's financials and turn them into structured text: headline metrics, movement, narrative, and unknowns. You don't invent a number, and you don't invent a cause. Every figure you output has to trace back to a figure in the input or a calculation built from figures in the input. Every narrative sentence either cites what it's based on, is labeled a stated assumption, or gets moved to the "couldn't figure out" section.

## Data input

This skill is file-in. Here's what it wants:

1. **Required**: the current period's P&L (or an equivalent financial export): revenue, cost of revenue/COGS, opex by category, and the resulting profit/loss line, for one stated period.
2. **Optional**: the prior period's P&L, same shape, for period-over-period movement. Without it, the movement section is limited to what the current period alone can show (more on that below).
3. **Optional**: plan/budget figures for the same period, for actual-vs-plan movement.
4. **Optional but recommended**: a short list of context notes straight from the CFO (e.g. "hired 3 engineers in March," "one-time legal fee in Q2"), used only as sourced narrative material, never as license to guess past them.
5. **Optional**: a previous board deck's finance section, to match its format (see "Matching a previous deck's format" below).

**If the required current-period P&L is missing, stop and ask for it.** Don't proceed on a plan-only or prior-only input. There's nothing to headline yet. Same call if the P&L is present but empty or effectively blank (every line missing or zeroed out with nothing else in the input to work from): stop and ask, rather than drafting a report over nothing.

**Before using any input figures, check that they add up.** If a stated subtotal doesn't match the sum of its own listed parts (a "Total opex" that doesn't equal the opex lines under it, a "Gross profit" that doesn't equal Revenue minus COGS), don't silently pick one number over the other. Flag the mismatch in "What this skill couldn't figure out" and say which two figures disagree, rather than trusting either one.

If a field in the input can't be read as a number (blank, garbled, mixed currency symbols in the same table, obvious placeholder text), don't guess at it or skip it silently. List it in "What this skill couldn't figure out" as unreadable, and say what it looked like.

## Matching a previous deck's format

If a previous board deck's finance section is supplied alongside the financials, use it as the template: same section order, same headings, same level of formality, same general length per section. Carry over the *shape*, never the *content*: every number, every sentence of narrative, and the could-not-determine list get rebuilt fresh from this period's input under the rules below. Nothing from the old deck's figures or commentary survives into the new draft; only its structure does.

If the previous deck's shape conflicts with a required element of this skill (for example, it has no "couldn't figure out" equivalent section), keep the previous deck's format everywhere else but still add that section. It's required output regardless of template, per Step 5. Say in your response that the section was added because this skill always includes it.

If no previous deck is supplied, fall back to the default structure in "Output structure" below.

## Step 1: Establish period and comparison basis

State plainly, at the top of the output:
- The period covered (e.g. "Q2 2026" or "March 2026"), taken from the input, never assumed from today's date.
- Currency and units (whole dollars, thousands, etc. Read this from the input; if it's ambiguous, flag it in "couldn't figure out" rather than guessing).
- What comparison basis you actually have: prior-period actuals, plan, both, or neither. If neither prior nor plan figures showed up, say so and just report the current period's absolute figures. Don't manufacture a comparison.

## Step 2: Headline metrics

Pull the metrics the board wants to see first: revenue, gross margin (if COGS is present), total opex, operating profit/loss, and cash position or burn if it's in the input. Only report metrics that exist in the input or can be computed from figures that exist in the input (gross margin from revenue and COGS, for instance). Never give a headline metric a made-up value. If something the board would expect (headcount, ARR) isn't in the input, don't fabricate it; put it in "couldn't figure out" instead.

Rounding: match the precision of the source data; don't manufacture false precision (no cents if the source is whole dollars). Say what rounding convention you used if you round for readability.

## Step 3: Period-over-period movement

For each headline metric, show the movement against whatever comparison basis you have (prior period, plan, or both):
- Absolute change and percentage change.
- If the comparison denominator is zero or the metric is new this period, don't compute a percentage. Write "n/a (new this period)" or "n/a (no prior-period base)" instead of dividing by zero or dropping the line quietly.
- If a metric shows up in the current period but not the comparison period (or the reverse), say so directly rather than treating the missing side as zero.

## Step 4: Narrative behind each movement

For each metric with a movement worth calling out (material in size, or one the board would ask about), write one to three sentences explaining it. Every sentence has to do one of:
- Cite a calculation from the input ("opex rose $42K, driven by a $38K increase in the marketing line").
- Cite a context note straight from the CFO, attributed as such ("per the CFO's note, this reflects the March engineering hires").
- Be labeled explicitly as an assumption, if you're inferring a plausible driver that wasn't directly stated, and even then, only when the input gives you a strong structural signal (the whole increase sits inside one named line item), never for a movement you can't localize to a line.

Never guess at a cause just from the size and direction of a movement. A spend spike with no line-level detail and no CFO note gets no narrative sentence. It goes to Step 5 instead.

## Step 5: What this skill couldn't figure out

This section runs on every single output. It's required, not a nice-to-have, and it never disappears. Even when everything traced cleanly, it says so plainly (e.g. "No material gaps this period; every headline metric and movement traced back to the input.").

List, plainly:
- Any board-expected metric missing from the input (headcount, ARR, NRR, cash runway, whatever wasn't supplied).
- Any movement from Step 3 that couldn't get a sourced sentence in Step 4 (the spend spike with no stated reason, the metric that moved with nothing in the data to explain it).
- Any subtotal that didn't reconcile with its own parts, and which two figures disagreed.
- Any field that couldn't be read as a number, and what it looked like.
- Any ambiguity in units, currency, or period boundaries that had to be flagged instead of assumed.
- Anything the CFO should send next time to close the gap ("a per-department opex breakdown would explain the marketing variance").

## Output structure

Default order, used when no previous deck is supplied to match: period and basis statement, headline metrics, period-over-period movement, narrative, couldn't-figure-out list. No slide layout, no chart placeholders, no speaker notes. This is the text a CFO edits into their own deck template. When a previous deck's format is supplied, follow "Matching a previous deck's format" above instead, but the couldn't-figure-out section is never dropped.

## Explicitly out of scope

This skill doesn't generate slides, PowerPoint, or Google Slides files. It doesn't produce charts or images. It doesn't cover the non-finance sections of a board deck (product, hiring, GTM). It's not a variance-report generation tool for the monthly close (see GL to Report for that) and it's not the investor/LP update (see Investor Update for that).

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/board-deck/).

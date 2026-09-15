---
name: qbo-inventory-reconciliation
description: >
  Checks a physical inventory count against what QuickBooks Online thinks
  is on the shelf. It takes a per-item quantity list that the bookkeeper
  pastes or uploads, pulls QBO's inventory asset records for the same
  period through the QuickBooks Online MCP
  (intuit/quickbooks-online-mcp-server), and reports the variance item by
  item instead of as one lump number. If a business tracks no inventory in
  QBO, it skips the check cleanly rather than erroring or reporting a
  variance that isn't real. It writes nothing to QBO. It's read-only by
  design. Use it whenever the user says "reconcile inventory", "check my
  physical count against QuickBooks", "inventory variance", "did we lose
  inventory", "shrinkage check", "compare counted inventory to QBO",
  "inventory reconciliation", or anything else that means they want to
  confirm a physical count against what QuickBooks records. Always use this
  skill for QBO inventory reconciliation work. Don't freehand a variance
  comparison without it.
license: MIT
---

# QBO Inventory Reconciliation

Check a physical inventory count against what QuickBooks Online has on the
books, item by item. Shrinkage and damage get caught before close, instead
of turning up later as an unexplained variance.

## Role

You are an inventory reconciliation assistant for a bookkeeper on
QuickBooks Online. You take the physical count that the bookkeeper hands
you. You pull QBO's own inventory asset records for the same period. You
report exactly where the two disagree, item by item.

You read the books. You never change them. Say so plainly and stop when a
business tracks no inventory in QBO at all. Never invent a variance where
there is nothing to reconcile.

## Before you start: confirm read-only access

This skill calls the QuickBooks Online MCP server
(`intuit/quickbooks-online-mcp-server`) for reads only. Before you run
this skill, confirm that the MCP starts with its write tools off:

```
QUICKBOOKS_DISABLE_WRITE=true
QUICKBOOKS_DISABLE_UPDATE=true
QUICKBOOKS_DISABLE_DELETE=true
```

That MCP server's own README documents these env var names as of this
skill's writing. MCP server flags change between releases. Confirm the
names against the version that you run. If you cannot confirm that the
write tools are off, tell the user to check before you proceed.

This skill never calls a `create_*`, `update_*`, or `delete_*` tool
itself. That rule holds whatever the MCP configuration says. The env vars
are a second guarantee. They do not replace this skill's own read-only
behavior.

## Step 1: Establish the Period and Count Cutoff

Ask the user for the reconciliation period if the user did not state it.
An example is "as of May 31, 2026", "Q2 2026 close", or "end of last
month". A physical count is a point-in-time snapshot. So anchor it to a
single as-of date, not to a date range. Ask for the specific count date
inside the range if the user gives a range.

Also ask whether the count happened at end of day, or at some earlier
point. This matters. A count can come before end of day. QBO's balance for
that same date can include receipts, sales, or adjustments posted later
that day. A comparison against QBO's full-day balance then reports those
later movements as inventory variance that never really happened.

**QBO's own transaction records cannot resolve this for you. Never promise
a clock-time netting-out that you cannot perform.** QBO exposes a
transaction's date at day granularity, not the time it happened. QBO data
alone cannot tell you when a receipt posted. A receipt before the
bookkeeper's 2pm count reads the same as one after it. So:

- A count taken at end of day raises no cutoff problem. Proceed normally.
  QBO's as-of-that-date balance already reflects a full day.
- A count taken at any other point in the day leaves two real options.
  Pick one explicitly with the bookkeeper. Never silently attempt a
  netting calculation that the data cannot support:
  1. Ask the bookkeeper to redo the count at end of day. Stop the run here
     and wait if the bookkeeper chooses this. Resume from Step 2 once the
     new end-of-day count arrives. Or
  2. Ask the bookkeeper for a timestamped movement log for that day. A
     point-in-time snapshot works too, if their system produces one. Such
     a log establishes what moved before the count and what moved after
     it.
- Say so plainly if neither option is available. Reconcile against QBO's
  end-of-day balance anyway. **QBO's transaction data cannot tell you
  which specific items moved that day.** It tells you only that the count
  was intraday, and that the comparison runs against a full-day balance.
  So flag EVERY item in the report as "count taken intraday, no movement
  log available. Variance may include later same-day movement". Never
  selectively flag only the items that "had same-day activity". QBO's
  day-granular data cannot tell you that per item.

## Step 2: Intake the Physical Count

Ask for the physical count as a per-item quantity list (pasted or
uploaded CSV/text; at minimum item name/SKU and counted quantity per
row). **Read `references/count-intake.md` before treating the count as
comparable to QBO's numbers** — unit-of-measure, scope, and
omission-means-zero checks, plus five row problems to flag back rather
than guess at. No photo/OCR counting.

## Step 3: Pull QBO's Inventory Asset Records

Pull the inventory asset report or item-level valuation for the as-of
date via the QuickBooks MCP. **Read `references/qbo-pull.md` first** —
pagination-to-completion and which fields to capture.

**Stop and tell the user that the pull failed, if this pull errors or
times out. Stop also if it returns a malformed response, or omits its
payload. Do not continue to Step 4.** A failed or absent pull is not the
same thing as "this business has no inventory tracked". Treating it as one
reports a false "nothing to reconcile". The business does carry inventory.
Its report call simply broke. That is a silent false-clean result. It is
worse than a false variance, because nobody has a reason to question it.

## Step 4: Confirm Whether Inventory Is Tracked At All

**Read `references/inventory-tracked-check.md` and follow it fully before
any "no inventory" conclusion.** In short: always run a separate,
paginated-to-completion item-list query, and stop only on a confirmed
zero-item list — never on an empty valuation pull alone (that gets
zero-filled and carried through Step 5 instead).

## Step 5: Calculate Variance By Item

**Read `references/variance-calculation.md` before computing any dollar
figure** — cost-basis derivation, zero/negative-quantity and
value-without-quantity handling, the average-cost-vs-FIFO caveat, and
netting a timestamped intraday log.

For every item in both sources: compute quantity variance (counted minus
QBO) and, where derivable, dollar variance; classify **Matched** (zero
variance), **Short**, **Over**, or **Flagged** (value-without-quantity or
unresolved intraday timing — Step 6). Never call a flagged item matched
just because quantities agree. Report every item, not only variances.
**Read `references/output-templates.md`** for the exact table format and
home-currency rule.

## Step 6: Flag Unmatched Items

List every item appearing in only one source. **Read
`references/unmatched-item-rules.md`** for the classification logic —
counted-only, QBO-only (branches on Step 2's omission convention),
value-without-quantity, intraday-no-log. **Read
`references/output-templates.md`** for the table format and which rows
the total excludes. Say so if nothing to flag — never omit the section.

## Output Sequence

1. The resolved reconciliation period or as-of date, and the count cutoff,
   confirmed with the user in Step 1
2. The flag-back from Step 2, if the physical count had rows flagged to
   the user. Those rows carry missing identifiers, duplicates, non-numeric
   quantities, negative quantities, or implausibly large quantities. That
   flag-back stops the run here until the bookkeeper resolves it. Nothing
   further runs on an unresolved count.
3. Otherwise, one of three things. The clean "no inventory tracked,
   skipping" statement from Step 4, which comes only after the separate
   item-count confirmation. Or a stop-and-report, if the valuation pull
   failed or contradicted the item-count confirmation, from Step 3 and
   Step 4. Or the full variance-by-item table from Step 5.
4. The unmatched items from Step 6, if the reconciliation ran
5. The total variance in the QBO company's actual home currency, if the
   reconciliation ran. It covers every item that appears in both sources
   and has a derivable cost basis. It leaves out items marked
   "unavailable" per Step 5, and the two single-source unmatched
   categories per Step 6.

## What this skill never does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never adjusts an inventory item's quantity or value in QBO.
- It never reports "no inventory tracked" from an empty valuation pull
  alone. It confirms with a separate item-count query first. It stops and
  reports the failure, rather than skipping, when the valuation pull
  itself errors, times out, or comes back malformed.
- It never reports a variance for a business genuinely confirmed to track
  no inventory in QBO. It states plainly that there is nothing to
  reconcile, and it stops.
- It never treats a genuinely empty count-against-QBO comparison as "no
  inventory tracked". That comparison is a real zero variance. It
  reconciles and reports the former. It skips only the latter.
- It never guesses a per-unit cost when QBO's own on-hand quantity is
  zero. It reports the dollar variance as unavailable instead.
- It never does photo-based counting or OCR counting. The physical count
  must already exist as a quantity list, pasted or uploaded.

## Eval Contract

### Spec

A correct run compares a bookkeeper-supplied physical count against QuickBooks Online's own inventory records for the same period and reports the variance item by item, quantity and dollars, with each item classified as Matched, Short, Over, or Flagged. It never derives a per-unit cost it does not have: an item with zero QBO on-hand quantity gets its dollar variance marked unavailable and stays out of the total dollar variance, with any stranded asset value cited as QBO's raw figure rather than a computed variance. It distinguishes a genuinely empty count-against-QBO comparison, which is a real zero variance, from a business that tracks no inventory, which it confirms with a separate item-count query before concluding. It changes nothing in QuickBooks Online.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

The hard-fail gate is evaluated over the run transcript and the output together, because a write call is a transcript fact. The scored table below is judged from the output alone. A condition appears in the gate or in the table, never in both.

**Hard-fail gate (check before scoring):** Any call to a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP fails the run regardless of total, as does any claim to have adjusted an inventory item's quantity or value. A run that wrote to QuickBooks is wrong regardless of what else it got right.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | No guessed cost basis | An item with zero QBO on-hand quantity has its dollar variance marked unavailable | A per-unit cost taken from another item, an average, or a round number | 1 |
| 2 | Unavailable items excluded from the total | Any item marked unavailable is left out of the total dollar variance | Such an item folded into the total | 1 |
| 3 | Stranded value flagged, not computed | Value-without-quantity cases classified Flagged, citing QBO's raw stranded asset value | Classified Matched because quantities agree, or reported as a computed variance | 1 |
| 4 | Empty comparison is not "no inventory" | A real zero variance is reported as reconciled; only a confirmed no-inventory business stops the run | A zero variance reported as "no inventory tracked" | 1 |
| 5 | No-inventory confirmed separately | "No inventory tracked" concluded only after a separate item-count confirmation | Concluded from an empty valuation pull alone | 1 |
| 6 | Failed pull stops the run | A valuation pull that errors, times out, or returns malformed data is reported as a failure | A failed pull treated as an empty result and skipped | 1 |

**Score to action:** 6/6 ship. 5 acceptable, note the gap. 3 to 4 borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail gate trip is a fail regardless of total.

### Self-Test

**Scenario A.** Period end 2026-06-30, single currency, count taken at end of day.

Pasted physical count:
- Widget A: 100
- Widget B: 40
- Widget C: 0

QuickBooks Online inventory records for the same date:
- Widget A: 105 on hand, $12.00 per unit
- Widget B: 40 on hand, $8.00 per unit
- Widget C: 0 on hand, $250.00 inventory asset value

- The output MUST classify Widget A as Short with a quantity variance of -5 and a dollar variance of -$60.00.
- The output MUST classify Widget B as Matched with a zero quantity variance and a zero dollar variance.
- The output MUST mark Widget C's dollar variance unavailable for lack of a cost basis and classify it as Flagged.
- The output MUST cite QBO's raw $250.00 value for Widget C rather than reporting it as a computed variance.
- The output MUST report a total dollar variance of -$60.00.
- The output MUST NOT include Widget C's $250.00 in the total dollar variance.
- The output MUST NOT derive a per-unit cost for Widget C from Widget A, from Widget B, or from an average.
- The output MUST NOT call any `create_*`, `update_*`, or `delete_*` tool, or state that it adjusted a quantity.

**Scenario B.** The inventory valuation pull for the period returns successfully with zero rows. The separate item-count query returns 0 inventory-type items.

- The output MUST state that concluding "no inventory tracked" requires a separate item-count confirmation, and MUST report that confirmation's result before drawing that conclusion.
- The output MUST distinguish this case from a count-against-QBO comparison that produced a genuine zero variance.
- The output MUST NOT report "no inventory tracked" on the strength of the empty valuation pull alone.
- The output MUST NOT report a reconciled zero variance as though a count had been compared against QBO records.

### Version

1.0.0

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-inventory-reconciliation/).

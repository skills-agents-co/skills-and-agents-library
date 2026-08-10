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

Ask the user for the physical count as a per-item quantity list. The user
can paste it in chat or upload it as a file, either CSV or plain text.
Each row needs at minimum:

- The item name or SKU
- The counted quantity

Confirm three things before you treat the count as comparable to QBO's
numbers:

- **The unit of measure.** The physical sheet may count in a different
  unit than QBO stores. An example is cases counted against units recorded
  in QBO. Ask the bookkeeper to state the conversion in that case. Or convert
  the count yourself with a stated conversion rate. Do either one before
  you compare quantities. Never assume that the units already match.
- **The scope.** QBO's inventory valuation may be company-wide while the
  count covers one location, or the reverse. Say so, and scope the
  comparison to what the bookkeeper actually counted. Never compare a
  partial count against a full-company QBO balance. Never report that
  difference as shrinkage.
- **Whether omission means zero.** Ask the bookkeeper directly. Does this
  list cover every inventory item they expected on hand? If it does, a
  missing item genuinely had none, and counts as a zero. Or does it list
  only what they found, so that a missing item was never checked? The
  answer decides how Step 6 treats a QBO item absent from the count. One
  reading makes it a real shortage, zero-filled. The other makes it
  genuinely uncounted, flagged and not zero-filled. Never assume either
  reading. A business that skips zero-stock items on a physical count is
  common. Treating that omission as a counted zero would report false
  shrinkage for anything the counter simply did not walk past.

This skill does not do photo-based counting or OCR counting. The count
must already exist as a list when the bookkeeper hands it over.

Flag a row back to the user before you continue in any of these cases.
Never guess at what the row meant. Never reconcile against a number that
is probably wrong:

- The count is missing item identifiers.
- The count has duplicate rows for the same item.
- A quantity is obviously non-numeric.
- A quantity is **negative**. That is a typo, or a signed-adjustment
  entry, not a real physical count. Nothing sits at negative units on a
  shelf.
- A quantity is implausibly large for the item described. An example is a
  quantity several orders of magnitude above every other row. That is a
  likely fat-finger or unit mix-up.

## Step 3: Pull QBO's Inventory Asset Records

Pull the inventory asset report, or the item-level inventory valuation,
for the stated as-of date with the QuickBooks MCP. The tool name and
report name depend on what the connected MCP server exposes. Check its
available tools before you assume a specific name. Use whichever one
returns the on-hand quantity and the value per inventory item as of a
date.

Follow the tool's pagination if the business has a very large item catalog
and the tool paginates its results. Never assume that the first page is
the whole inventory. Per Step 4, an item missing from this pull gets
zero-filled rather than treated as unmatched. So a truncated pull here
does not surface as a false unmatched or discontinued item. It surfaces as
a false quantity overage with a dollar figure attached, which is harder to
spot. The item-list query in Step 4 may return more inventory items than
this pull returned rows. Treat that as a signal that the valuation pull
was truncated. Confirm that you exhausted pagination before you proceed.

**Stop and tell the user that the pull failed, if this pull errors or
times out. Stop also if it returns a malformed response, or omits its
payload. Do not continue to Step 4.** A failed or absent pull is not the
same thing as "this business has no inventory tracked". Treating it as one
reports a false "nothing to reconcile". The business does carry inventory.
Its report call simply broke. That is a silent false-clean result. It is
worse than a false variance, because nobody has a reason to question it.

Capture these fields for each inventory item that QBO returns. Capture the
item name or SKU. Capture the quantity on hand. Capture the asset value on
hand as of the period. An item may show a value with a zero quantity, or
the reverse. Capture both as given. Do not infer a per-unit cost yet. That
happens in Step 5, and only for items whose inputs support it.

## Step 4: Confirm Whether Inventory Is Tracked At All

**Run the item-list query every time. Do not run it only when Step 3's
valuation pull comes back completely empty.** Some valuation report
variants exclude items with zero recent activity, or with zero on-hand
quantity. So a valuation pull can return some items and stay non-empty. It
can still omit an item genuinely configured in QBO with no recent
movement. Suppose you ran this check only on a fully empty pull. That
omitted item would flow straight to Step 6 as "unmatched". That label
looks like a naming mismatch or a discontinued item. It is really a QBO
item sitting at zero on-hand quantity. It is a real overage if the
physical count shows any units for it.

So always run a separate, simpler query. Use an item list, or an item
search filtered to Inventory-type items. That query gives you the complete
set of inventory items that QBO has configured. It is independent of
whatever the valuation report's own filtering logic includes. **Follow
this query to completion if it paginates, the same way Step 3 requires for
the valuation pull.** An item beyond the first page is otherwise absent
from the authoritative set. Its physical count would then read as
unmatched, instead of reconciling as a configured zero-balance item.

This item-list query reflects QBO's *current* configuration when the
reconciliation date is not today. It does not reflect the item list as it
stood on the as-of date. An item created after the reconciliation date
appears here, and genuinely had no balance to report as of that date. Do
not flag its absence from the count as an omission. An item deactivated
since then may drop out of a default item-list query entirely. Include
inactive items if the MCP tool supports that. A deactivated item can still
carry a real balance as of a past reconciliation date.

- Stop here if that confirms that zero inventory-type items exist at all.
  Report plainly: "This QuickBooks account has no inventory items tracked,
  so there's nothing to reconcile against a physical count. Skipping this
  step." Do not treat this as a variance of zero. Do not error.
- That query may confirm that inventory items DO exist, while Step 3's
  valuation pull came back completely empty anyway. Distinguish a
  **legitimate** empty result from a **failed** one there. Some valuation
  report variants legitimately exclude every item when the whole catalog
  has zero balance or zero recent activity. Step 3 already stops on a
  genuine pull failure. A genuine failure is an error, a timeout, or a
  malformed or missing payload. So the pull itself succeeded and returned
  no rows if you reached this bullet at all. Treat that as the legitimate
  case. Zero-fill every item on the authoritative item list. Set its
  quantity and its value to zero, by the same rule as the next bullet.
  Continue through Step 5 rather than stopping. Stop and tell the user
  that something is wrong in one case only. The pull's own response must
  indicate a genuine failure per Step 3. An empty-but-successful response
  is not that.
- The item list AND the valuation pull may both return items. Use the item
  list then as the authoritative set of "items QBO knows about". Take any
  item on that list that is missing from the valuation pull's results.
  Treat its QBO on-hand quantity and asset value as zero, not as "no
  data". It is a real QBO item that the valuation report did not happen to
  include. This rule covers a physical count against a zero-activity item.
  Step 5 and Step 6 then report a quantity overage, not an unmatched or
  discontinued item.

QBO's inventory asset pull may return items where every quantity is zero.
The counted list may also match exactly. Either case is a **genuine
zero-variance result**. It is not the same thing as "no inventory
tracked". Continue through Step 5. Report a clean reconciliation with no
variance, rather than skipping.

**One exception applies. A zero-quantity item may carry a nonzero asset
value in QBO.** Step 5's value-without-quantity rule covers that case.
That is a real stranded-value discrepancy, not a clean result, even though
the quantities match. The distinction matters. No inventory items
configured means that inventory is not set up in QBO at all. A populated
report with matching numbers and no stranded value means that inventory is
tracked and happens to check out. Treating the second case as a skip would
hide a real reconciliation result, however uneventful.

Step 4's query builds the authoritative item list. The Step 2 physical
count may hold items that match no inventory item on that list. Do not
silently drop them. List them separately as unmatched, in Step 6. A
genuinely untracked business would have no QBO items to match against at
all. A handful of unmatched items in an otherwise populated report usually
means a naming mismatch, or a discontinued item.

## Step 5: Calculate Variance By Item

Determine each item's per-unit cost before you compute a dollar variance.
Divide QBO's asset value by its on-hand quantity. Do this only when QBO's
quantity is strictly greater than zero.

**A negative QBO on-hand quantity is not a valid divisor either.** QBO
occasionally shows negative inventory, as when a sale is recorded before
its receipt. A division of asset value by a negative quantity produces a
per-unit cost with no real meaning. So treat a negative QBO quantity the
same as a zero quantity for cost-basis purposes. No per-unit cost is
derivable from it.

Take an item whose QBO on-hand quantity is zero or negative **and whose
physical count is positive**. Asset value ÷ quantity is undefined there.
That item's own QBO record yields no valid per-unit cost. Do not guess a
cost from another item. Do not average. Do not assume a round number.
Report the quantity variance for that item normally. Mark the dollar
variance "unavailable: no cost basis in QBO" instead of computing a
number. Do not fold that item into the total dollar variance.

**This per-unit cost is a weighted average, not QBO's own FIFO layer
valuation.** QBO's inventory accounting values a shortage or an overage
with FIFO cost layers. It does not use a flat average of total value over
total quantity. An item can hold inventory acquired at different costs
over time. The true FIFO-layer value of its shortage or overage can then
differ from this average-cost estimate. State every dollar variance in the
report as an estimate derived from average cost. Never state it as QBO's
own FIFO-accurate figure. The bookkeeper then reads it as directional
rather than exact for an item with cost history.

**Do not stop at "quantities match, call it clean" here.** That applies
when QBO's quantity is zero AND the physical count is also zero. Check whether QBO's asset
value for that item is nonzero despite the zero quantity. A nonzero value
there is a real bookkeeping discrepancy. It is a stranded dollar balance
with nothing behind it, even though there is no quantity variance.

There is still no per-unit cost to derive there, because the quantity is
zero on both sides. So **do not compute or report a dollar variance figure
for this item**. Mark its dollar variance "unavailable: no cost basis",
like any other zero-quantity item. Exclude it from the total the same way.
Flag it explicitly in Step 6 as a value-without-quantity discrepancy. Cite
QBO's raw stranded asset value there, not a computed variance. The
bookkeeper then sees the number without it folding into the variance
total. Do not classify the item as a clean match just because the
quantities happen to agree.

**Step 1 may have identified an intraday count, and the bookkeeper may
have supplied a real timestamped movement log or snapshot. Use that log to
net the identified movements out of the quantity variance.** Step 1's
option 2 covers that log. The log is real point-in-time data, so it is
safe to use precisely for quantity. For the dollar variance, net the cost
basis alongside it. Do that **only if the log also states a per-unit cost
for those specific movements.**

Suppose the log nets a quantity movement and states no per-unit cost for
it. Do not fall back to QBO's end-of-day average cost for that item. That
fallback is the exact defect this rule prevents. The netted quantity and
an un-netted cost basis would silently disagree. Report the quantity
variance with the netted figure instead. Mark that item's dollar variance
"unavailable: cost basis not established for the log's netted movements".
Exclude it from the total, by the same convention as the zero-QBO-quantity
case above.

**Do not attempt to net anything out if no timestamped log exists, and you
have QBO's own records alone.** QBO's transaction dates are day-granular,
not clock-time. So QBO data alone gives no reliable way to tell which
items actually had same-day activity. It gives even less on whether that
activity fell before or after the count. Report every item's quantity
variance and dollar variance as computed against QBO's end-of-day balance.
But flag every item explicitly, per Step 1: "count taken intraday, no
movement log available. This item's variance may include movement after
the count, not just before it." Never silently net out activity on a guess
about timing that you cannot confirm. A wrong guess is worse than an
honest flag on every item.

Do this for every item that appears in both the physical count and QBO's
pull:

1. Compare the counted quantity against QBO's on-hand quantity.
2. Compute the quantity variance, which is the counted quantity minus
   QBO's quantity. Compute the dollar variance too, where the cost basis
   rule above lets you derive one.
3. Classify the item as one of these:
   - **Matched**: zero variance
   - **Short**: counted less than QBO, so possible shrinkage or damage
   - **Over**: counted more than QBO, so a possible unrecorded receipt or
     a prior miscount
   - **Flagged**: a value-without-quantity discrepancy, or an unresolved
     intraday-timing case. See below.

Never classify a flagged item as **matched** just because its quantities
happen to agree. Quantities that agree are not the same thing as an item
that is clean.

Report every item, not only the ones with a variance. The acceptance bar
here is item by item, not an aggregate number.

Use the QBO company's actual home currency for every dollar figure below.
Never hardcode a `$`. Pull or confirm the company's home currency. Render
its symbol or its currency code, such as `CAD` or `€`, instead of assuming
USD. Ask the bookkeeper directly if you cannot determine the home currency
from QBO, or if the file mixes currencies. Never default to USD.

```
## Inventory Variance, as of [period end date]

| Item | Counted Qty | QBO Qty | Qty Variance | Variance ([currency]) | Status |
|------|-------------|---------|--------------|------------------------|--------|
| …    | …           | …       | …            | [symbol]… / unavailable: no cost basis / unavailable: cost basis not established for netted movements | Matched / Short / Over / Flagged |

Total variance ([currency]): [symbol]X,XXX.XX (leaves out any item marked "unavailable" for either cost-basis reason, and the two single-source Unmatched Items categories below)
```

## Step 6: Flag Unmatched Items

List every item that appears in only one source in a dedicated section.
List the two special cases below there too:

- Counted, and not found in QBO's inventory items. That means a naming
  mismatch, or a discontinued item. It can also mean something counted
  that nobody set up in QBO as an inventory item.
- In QBO's inventory pull, and not in the physical count. **What you do
  here depends on the omission convention that Step 2 confirmed.** The
  bookkeeper may have said the count is exhaustive, so a missing item
  means a real counted zero. Zero-fill this item's counted quantity in
  that case. Run it through Step 5 as a normal item. A nonzero QBO
  quantity then correctly shows as a shortage. The bookkeeper may instead
  have said the count lists only what they found. A missing item then
  means that nobody checked it. List it here as genuinely uncounted in
  that case, rather than zero-filling it. Treating "not checked" as
  "checked and found zero" would report false shrinkage.
- **Value without quantity**, from Step 5. QBO shows zero on-hand quantity
  for an item. The physical count also shows zero, or nobody counted the
  item at all because they believe there is none. QBO's asset value for
  that item is nonzero. Flag this as a stranded-value discrepancy. Cite
  QBO's raw asset value as the amount. Do this even though there is no
  quantity variance and no computed dollar variance to report.
- **Intraday timing, no supporting log**, from Step 1 and Step 5. The
  count was not taken end-of-day and no timestamped movement log was
  available. Flag every item in the report this way. Do not flag only the
  ones with observable "same-day activity". QBO's day-granular data cannot
  tell you per item whether it moved that day. Flag each one as "variance
  may include post-count movement", even though you still report a number.

```
## Unmatched Items

| Flag type | Item | Qty / Value | Issue | In variance total? |
|-----------|------|-------------|-------|---------------------|
| Counted-only / QBO-only / Value-without-quantity / Intraday-no-log | … | … | … | Y/N |
```

The variance total above leaves out three kinds of row. It leaves out the
two genuine single-source rows, counted-only and QBO-only. Neither one has
a matching item on the other side. It leaves out the
value-without-quantity row. Mark all three `N`. The single-source rows
have nothing on the other side to compute a variance against. The
value-without-quantity row has zero quantity on both sides, so there's no
per-unit cost and no dollar variance to compute. Its stranded asset value
shows in the Issue column, and that raw figure never folds into the total.

The intraday-no-log row **is** in the variance total. Step 5 still
computes and reports a real number for it. It's flagged here only as a
timing caveat, not excluded. Mark that one `Y`.

Say so plainly if there is nothing to flag. Never omit the section.

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

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-inventory-reconciliation/).

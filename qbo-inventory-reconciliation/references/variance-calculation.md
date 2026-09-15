# Variance Calculation Detail (Step 5)

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

Classify the item as one of these:

- **Matched**: zero variance
- **Short**: counted less than QBO, so possible shrinkage or damage
- **Over**: counted more than QBO, so a possible unrecorded receipt or
  a prior miscount
- **Flagged**: a value-without-quantity discrepancy, or an unresolved
  intraday-timing case. See below.

Never classify a flagged item as **matched** just because its quantities
happen to agree. Quantities that agree are not the same thing as an item
that is clean.

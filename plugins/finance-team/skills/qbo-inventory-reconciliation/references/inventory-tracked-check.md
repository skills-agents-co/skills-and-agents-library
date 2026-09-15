# Confirm Whether Inventory Is Tracked At All (Step 4 detail)

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

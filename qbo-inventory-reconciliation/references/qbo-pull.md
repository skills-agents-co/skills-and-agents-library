# QBO Valuation Pull Detail (Step 3)

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

Capture these fields for each inventory item that QBO returns. Capture the
item name or SKU. Capture the quantity on hand. Capture the asset value on
hand as of the period. An item may show a value with a zero quantity, or
the reverse. Capture both as given. Do not infer a per-unit cost yet. That
happens in Step 5, and only for items whose inputs support it.

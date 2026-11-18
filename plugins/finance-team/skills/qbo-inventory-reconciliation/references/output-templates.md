# Output Table Formats (Steps 5 and 6)

## Inventory Variance table

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

Total variance ([currency]): [symbol]X,XXX.XX (leaves out any item marked "unavailable" for either cost-basis reason, any item marked "QBO balance unavailable", and the two single-source Unmatched Items categories below)

Name each item left out because its QBO balance is unavailable on the total-variance line, for example "left out: Widget D (QBO balance unavailable)". For a long list, name the first 20, then "and N more".

If no item has a computed variance, print "Total variance ([currency]): not computable: [reason]" instead. Print the actual reason: "no QBO balances returned" (the pull came back empty), "no item in both sources", or "no cost basis for any item". Never print $0.00 then. State that no item was reconciled. ("QBO balance unavailable" means QBO gave no balance for the item. "Unavailable" in the Variance column means no cost basis.)
```

## Unmatched Items table

```
## Unmatched Items

| Flag type | Item | Qty / Value | Issue | In variance total? |
|-----------|------|-------------|-------|---------------------|
| Counted-only / QBO-only / QBO-balance-unavailable / Value-without-quantity / Intraday-no-log | … | … | … | Y/N |
```

The variance total above leaves out four kinds of row. It leaves out the
two genuine single-source rows, counted-only and QBO-only. Neither one has
a matching item on the other side. It leaves out the
QBO-balance-unavailable row. Its QBO quantity and value are unknown, so
there is nothing to compute a variance against. It leaves out the
value-without-quantity row. Mark all four `N`. The single-source rows
have nothing on the other side to compute a variance against. The
value-without-quantity row has zero quantity on both sides, so there's no
per-unit cost and no dollar variance to compute. Its stranded asset value
shows in the Issue column, and that raw figure never folds into the total.

Under the "count lists only what was found" convention, items that are
absent from both the valuation pull and the physical count share one
summary flag row: the count of items and their names, up to 20, then "and
N more". The row tells the bookkeeper to check those items' as-of balances
in QBO. Under the exhaustive-count convention (absent means counted zero),
each of those items keeps its own row: counted 0, QBO balance unknown. An
item with a physical count keeps its own `QBO-balance-unavailable` row.
When the valuation pull is empty, emit one summary flag ("valuation pull
returned no rows; all N items unavailable") instead, whatever the count
covers.

The intraday-no-log row **is** in the variance total. Step 5 still
computes and reports a real number for it. It's flagged here only as a
timing caveat, not excluded. Mark that one `Y`.

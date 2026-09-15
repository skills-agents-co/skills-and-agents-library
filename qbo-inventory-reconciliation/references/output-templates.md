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

Total variance ([currency]): [symbol]X,XXX.XX (leaves out any item marked "unavailable" for either cost-basis reason, and the two single-source Unmatched Items categories below)
```

## Unmatched Items table

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

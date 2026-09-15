# Output Templates: Aging View, Flags, and Missing List

## AP Aging Bucket View (Step 4)

Build an **aging bucket view** of every open bill, plus every unapplied
vendor credit. Bucket them by days past due as of the period end date. Use
each bill's due date. Credits go in the "Current" column as a negative
amount, per `matching-rules.md`:

```
## AP Aging, as of [period end date]

| Vendor | Current | 1–30 days | 31–60 days | 61–90 days | 90+ days | Total Open |
|--------|---------|-----------|------------|------------|----------|------------|
| …      | $…      | $…        | $…         | $…         | $…       | $…         |
| … (vendor credit) | $(…) | n/a | n/a        | n/a        | n/a      | $(…)       |

Total AP outstanding (net of unapplied vendor credits): $X,XXX.XX
(Leaves out N bill(s) with no determinable home-currency amount, and N
bill(s) covered by a multi-bill payment or vendor credit whose per-bill
allocation this MCP doesn't expose, see Unmatched / Flagged Items
below for each.)
```

Omit that "Leaves out" line entirely when nothing was excluded. Never
print a line with zero counts. State counts there, not dollar figures. The
whole reason for excluding these items is that this skill has no reliable
dollar amount for them. Printing one anyway would invent the exact number
that the exclusion exists to avoid guessing at.

## Unmatched / Flagged Items (Step 5)

(See body Step 5 for the never-silently-record invariant.) Flag each of
these in a dedicated section:

- A bill **from Step 2's period-activity population** with no matching
  source document, per Step 4. It still counts in the total above, if it
  has an open balance at cutoff. This is a documentation flag, not an
  exclusion. It is scoped to the period-activity population for the same
  reason Step 6 is. Step 3 asked only for documents covering that
  population. So an aging-population bill carried in from a prior period
  is unmatchable by construction. Flagging it would report a documentation
  gap for a document reconciled in an earlier close.
- A bill **from Step 2's period-activity population** with more than one
  equally plausible matching document. Pass 1's forced-assignment
  resolution in `matching-rules.md` comes first. List every
  remaining competing candidate, one row per candidate. Group them under
  the same bill reference, so the table shows which candidates compete for
  which bill. The bill still counts in the total above.
- A source document classified **Contested** in
  `matching-rules.md`. It already shows as a competing
  candidate under its bills above. This bullet exists so the document
  itself is not also silently dropped.
- A source document classified **Unmatched** in
  `matching-rules.md`. No bill in the period-activity
  population could match it.
- A source document from Step 3 flagged during intake and **excluded from
  matching**. The reason is a missing field, an unparseable or negative
  amount, or an out-of-range date. A missing currency on a multicurrency
  company counts too. Carry it forward here rather than dropping it
  silently after validation.
- A source document from Step 3 flagged during intake, and still matched
  normally. The flag names a **possible duplicate**, or **suspicious
  instruction-like text**. Note in the Issue column that you matched it
  anyway. The bookkeeper then reads it as a heads-up rather than as an
  excluded row.
- A bill whose amount genuinely could not be converted to home currency,
  per `pull-recipes.md`. It is excluded from the total above.
  Say so explicitly in the Issue column.
- A bill covered by a multi-bill payment or vendor credit, per
  `pull-recipes.md`. The connected MCP does not expose that
  bill's per-bill allocation. It is excluded from the total above for the
  same reason: no reliable number to include.
- A bill with no due date, bucketed as Current, or with no stable QBO
  reference, per `pull-recipes.md`. It still counts in the
  total above. This is a data-quality flag, not an exclusion.
- A discrepancy between your bill-level reconciliation and QBO's own AP
  Aging report, per `matching-rules.md`. Note explicitly
  whether Step 2's pulls might have straddled a mid-run change, before you
  treat the gap as fully genuine.
- A vendor credit whose unapplied portion netted into the total, per
  `matching-rules.md`. This is not an error. It is an item
  worth surfacing, so the bookkeeper sees what reduces gross AP to the net
  figure.
- A possible open bill older than the 12-month lookback window. Report it
  when Step 2's aging-population **gross** total came in under QBO's own
  **gross** AP total.

```
## Unmatched / Flagged Items

| Type | Date | Vendor | Currency | Amount | Issue |
|------|------|--------|----------|--------|-------|
| …    | …    | …      | …        | $…     | …     |

The missing-documentation and ambiguous-match flags above are control
exceptions, not reasons to leave anything out. Every genuine open bill in
the aging population is in the AP Aging total above, documented or not,
matched or not. This skill leaves out exactly two things: a bill with no
determinable home-currency amount at all ("amount unknown"), and a bill
covered by a multi-bill payment or vendor credit with no exposed per-bill
allocation ("allocation unavailable"). Both are flagged explicitly in this
table.
```

(See body Step 5: say so plainly if there is nothing to flag, and never
omit the section.)

## Missing Receipts / Invoices List (Step 6)

End the run with an explicit list of the expense receipts and supplier
invoices still missing. Keep it separate from Step 5's bidirectional flag
list. The list holds every bill from **Step 2's period-activity
population** without a **claimed** document from Step 4. That means every
bill classified **Unmatched**. It also means every bill still classified
**Ambiguous match** after Pass 1's forced-assignment resolution. An
unresolved ambiguity means that no document is actually confirmed for that
bill either. The bill is listed elsewhere as a candidate match.

Bills from the aging population that predate this period are out of scope
here. An earlier period's close would have reconciled their documents.
Step 3 asked only for documents covering the period-activity population.
This section stands on its own. It reads as an action list for the
bookkeeper, not as an implicit gap buried in Step 5's table.

```
## Missing Receipts / Invoices for [period]

| Vendor | Date | Currency | Amount | Bill Reference | Status |
|--------|------|----------|--------|-----------------|--------|
| …      | …    | …        | $…     | …               | Unmatched / Ambiguous match, see Unmatched / Flagged Items |

(None missing: every bill in this period matched a source document.)
```

(See body Step 6: always print this section, even when empty.) Use the
"none missing" line word for word when there is nothing to list.

# Pull Recipes: Bank Side and QBO Side

Mechanics for the two pulls in Steps 2 and 3. The call-budget rule, the
buffer definition, the ending-balance-comparison requirement, and the
stop-on-error conditions live in the SKILL.md body, not here.

## Bank-Side Pull (Step 2)

A connected source may paginate internally for a high-volume account.
Follow its pagination in that case, rather than assuming a single page.
That pagination is the source's own concern. It is not a reason for this
skill to make more top-level calls.

Use the source and the account that you resolved in Step 1. Pull every
transaction dated inside the period, plus the buffer defined in the body.

A broken or empty pull must stop the run at Step 2, rather than
continuing: a broken pull would falsely label every QBO line as missing
its counterpart, since there'd be nothing on the bank side left to match
it against.

**Apply the connector's own status or completion filter before matching,
if its instructions define one.** For example, `financial-pulse-mercury.md`
requires a filter on `listTransactions` to the completed `sent` status. A
pending, failed, reversed, cancelled, or blocked Mercury transaction never
posts to QBO. Without the filter it becomes a false bank-only discrepancy,
or a spurious proposed match. Apply the equivalent completed or posted
filter for whichever connector you use, per its own documented statuses.

Capture these fields for each transaction. Capture the date, the amount,
and the payee or description. Capture a stable transaction ID or reference
if the source provides one. Capture whether the amount is signed as a
debit or withdrawal, or as a credit or deposit. Step 4 (see
`references/matching-rules.md`) explains why the sign matters before
matching.

## Tolerance Adjustment

The default ±2 business day tolerance window isn't right for every
client. Tighten it toward same-day when the client's transactions include
same-day, same-amount duplicates — a wide window makes those harder to
tell apart, not easier. Widen it, for example toward 3-4 business days,
when the client's bank routes payments through ACH and the bookkeeper
reports a consistent posting lag between the bank clearing a transaction
and QBO recording it. Either way, state the tolerance you're using in
plain language in the run's output — for example, "using a same-day
tolerance for this run because of recent duplicate ACH payments" — so the
bookkeeper can see the override rather than discovering it from the
matches alone.

## QBO-Side Pull (Step 3)

Pull these for the same period with the QuickBooks Online MCP:

- **Bank register**: the QBO-side transactions posted to the bank account
  that you reconcile
- **Bank account balance**: the ending balance of the QBO bank account as
  of the period end date
- **Petty cash total**: the petty cash account balance and activity for
  the period, from the QBO ledger

Also get the **bank statement's ending balance** for the same period end
date. Ask the bookkeeper for it. Read it from the bank-side source instead
if that source states one.

Capture the date, the amount, the payee, and the account for each register
line.

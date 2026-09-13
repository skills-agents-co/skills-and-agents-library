# Balance Sheet Pull and Comparison (Step 4)

See SKILL.md Step 4 for when to run this pull: twice, as of the end of the
current period and as of the end of the prior period resolved in Step 1.

Extract these line items for both periods from the two balance sheet
snapshots:

- **Loans**: notes payable, current and long-term
- **Accrued expenses**: accrued liabilities, and accrued payroll when the
  report breaks it out separately from the payroll figure in Steps 2 and 3
- **Deferred revenue**: unearned revenue
- **Equipment and fixed assets**: net of accumulated depreciation, when
  the report shows that separately

**Several accounts in one category is normal, not ambiguous.** A bank note
and a vehicle loan are both real Loans accounts. Several depreciation
schedules are all real Equipment and fixed assets accounts. Include every
account that you can clearly classify into one of the four categories. Put
each one on its own detail row when the client has more than one. One
account can rise while another falls. Separate rows keep both moves
visible. A single blended row would net them out.

Reserve "ambiguous" for an account whose category assignment is genuinely
unclear. An example is an account that you cannot tell apart as a loan or
an accrued expense. Never apply "ambiguous" to a category that merely
holds more than one valid account.

Never guess which account to use in two cases. The first case is a chart
of accounts with no account that obviously matches one of the four
categories. The second case is an account whose category assignment is
genuinely unclear. That case does not cover "more than one clearly
classified account". In either case, state plainly which category has no
clear account. List the account names that you use for the categories you
did match. The bookkeeper then confirms the mapping instead of trusting it
silently. Mark the unmatched category **"unavailable: no clear account
match"** for both periods. Never report it as a $0 balance. A genuine $0
balance and a missing account look identical in a table unless you say
which one happened.

**The same rule applies in reverse when an account that you matched in the
prior period is absent from the current-period snapshot.** An example is a
fully repaid loan. A balance sheet report can omit its zero-balance
account entirely rather than show it at $0. The account name is missing
from the current pull. Do not fall back to "unavailable: no clear account
match" for that reason alone. That would suppress a real decrease to zero.

Do this instead. Keep the account mapping that you already established for
that category in the prior period. Then confirm which of two things
happened. The current period genuinely has no balance there. Report the
current balance as **$0, confirmed**. Compute the decrease normally. Or
QBO renamed or restructured the account itself. State that plainly. Mark
it unavailable, the same as an unmatched category. Never guess between the
two. Say so and ask the user if the pull does not tell you which one
happened.

Compute the period-over-period change for each line item with a real
balance in both periods. The change is the current balance minus the prior
balance. Report it in dollars and in percent.

An item is new this period when the prior balance is $0. It is also new
when the account did not exist last period. The dollar change is still
valid for a new item. The percentage change is undefined. Report it as
**"new this period"** instead of a percentage.

List the changes for every one of the four categories, including changes
close to zero. The acceptance criteria call for a full listing, not only
the flagged subset.

**Flagging threshold.** The threshold is **$5,000 or 10% of the absolute
value of the prior period's balance, whichever is smaller**. Flag a change
as needing the controller's review when its **absolute** dollar or
percentage change exceeds that threshold. Take the *smaller* of the two
deliberately, never the larger. A small account with a $1,000 prior
balance has a 10% threshold of only $100. That is tighter than the $5,000
floor. So a proportionally large move on a small account still gets
caught, even when the dollar amount looks trivial.

**Use the absolute value of the prior balance itself when you compute the
10% threshold. Do not use the change alone.** A prior balance can be
negative, as in a debit-balance liability account. Ten percent of a
negative number is itself negative, which would make even a $0 movement
register as exceeding it. A $30,000 decrease crosses this threshold
exactly as much as a $30,000 increase does. Compare magnitude against the
threshold, not the signed value, on both sides of the comparison. Keep the
signed value for display, so a decrease still shows as negative in the
table. Only the flagging decision uses absolute values throughout.

This threshold is again a stated, generic default. Nobody tuned it to any
one client's scale. State the threshold explicitly in your output every
time you run this check. Tell the user to adjust it once real client data
is available. A $5,000 swing may be trivial for one business and material
for another. "Whichever is smaller" may also be too sensitive for a client
with many small accounts. That is a real tradeoff to revisit with real
data, not a bug. Every flagged item names what changed and by how much.
Report the amount in dollars and in percent. Report "new this period"
instead where that applies.

**Apply only the $5,000 flat-dollar leg to a "new this period" item. The
10% leg is undefined against a $0 prior balance. Never treat that leg as
$0.** With a $0 prior balance, 10% of it is $0, which would flag any
nonzero new item however trivial.

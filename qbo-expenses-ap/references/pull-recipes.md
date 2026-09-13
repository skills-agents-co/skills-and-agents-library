# Pull Recipes: Step 2's Five Entity Pulls

**This skill reconciles vendor Bills. It does not reconcile every kind of
QBO expense record.** It never looks at a Purchase or an Expense
transaction entered directly against a bank or credit card account. Only a
Bill qualifies. Check whether the business records some spend that way. If
it does, tell the bookkeeper plainly, before you start, that those
transactions are out of scope. Never imply full expense coverage.

AP Aging is a point-in-time balance as of a cutoff date. It is not a
period-dated list. Pull with that in mind. Do not filter everything to
"dated within the period".

Pull both bill populations:

- **Bills (aging population)**: the MCP's entity-search tool may filter
  directly by open or unpaid status as of a date. Prefer that tool. That
  is the bounded, correct way to get this population. The tool may have no
  such filter, and may filter by transaction date alone. Only then widen
  the pull to cover the prior 12 months before the period end. Do not
  widen it to "as far back as the tool allows", which is unbounded. Then
  filter those results to open-as-of-cutoff yourself.

  **An older bill may exist beyond the window. Never take "the oldest bill
  this 12-month pull returned is still open" as your signal for that.**
  That signal is unreliable by construction. The oldest bill inside the
  window can happen to be paid. A genuinely older bill outside the window
  can still be open. The pull cannot see past its own boundary either way.

  Instead, always cross-check this population's **gross** total against
  the **AP Aging** report pulled below. The gross total is the sum of open
  bills, before you net any vendor credit. QBO computes the AP Aging
  report independently of this skill's own lookback window. QBO's AP Aging
  report typically also exposes a bills-only or gross-payable figure
  alongside its credit-netted total. Use that gross figure for this
  specific comparison. Do not use the netted one.

  A gap appears when QBO's gross figure exceeds the gross sum of open
  bills that this pull found. That gap is direct evidence of a bill, or
  several bills, that this pull's window missed. Tell the bookkeeper so
  explicitly. Suggest that they check for an open bill older than 12
  months. Suggest it whatever the oldest bill in this pull's own results
  happens to be.

  **A gross-to-gross comparison matters here. Never compare this pull's
  gross bill sum against QBO's credit-netted total.** An unrelated vendor
  credit would then close the gap by coincidence. That credit would mask a
  genuinely missed older bill.
- **Bills (period-activity population)**: every bill dated within the
  stated period, whatever its current open or paid status. The same
  entity-search tool may support a plain date-range filter. This is then a
  second, separate call with the period's own date range. Do not use the
  12-month aging window for it. A bill can appear in both populations, as
  an in-period bill still open at cutoff. That is expected. It is not a
  duplicate to remove. Do not double-count it in Step 4's total, which
  draws only from the aging population.
- **Bill Payments**: **do not pull every payment ever recorded through
  the period end date. That is unbounded on a long-lived company.** Scope
  this pull to payments linked to a bill already in one of the two
  populations above. Take these two paths in preference order:
  1. Use the MCP's payment tool to fetch by linked bill ID, or a similar
     bounded relationship, if it supports that. Stay within the 50-bill
     fan-out cap from Step 2's call budget.
  2. Otherwise, or when the populations exceed that cap, pull payments by
     date range. Match them by linked bill ID against the populations that
     you already hold. Discard anything unrelated. **That date range must
     span the full aging lookback window, through the period end date.
     That is the same 12 months before the period end that the aging
     population itself covers. It is not the stated period plus a short
     lookback.** An aging-population bill carried in from eight months ago
     may have been partially paid seven months ago. A pull scoped to the
     period plus 30-60 days never sees that payment. Step 4 then
     reconstructs that bill's cutoff balance from its face amount. It
     overstates both the bill's aging row and total AP. The window that
     finds the bill has to be the window that finds its payments.

  The aging population may come from a status filter rather than a
  12-month date pull. Path 1 of the Bills bullet above describes that.
  There is then no lookback window to mirror. In that case, take one of
  two routes. Fetch payments per bill inside the fan-out cap. Or pull
  payments over the prior 12 months through the period end. Then filter
  them to the populations that you hold. Never scope the payments pull
  more narrowly than the oldest bill that you age.

  You need the payments to compute each open bill's balance as of the
  cutoff. You do not need them only to match against Step 3's documents.
  **Capture the applied amount per bill on each payment. Do not capture
  only the payment's total and its list of linked bill IDs.** A single
  Bill Payment commonly covers several bills at once, each for a different
  amount. You cannot recover how much of it applies to any one bill if you
  keep only the payment's total. Subtracting the full payment total from
  every linked bill double-counts it. Dividing it evenly does not recover
  QBO's actual allocation.

  **Use the payment-to-bill line-item breakdown if the MCP's payment tool
  exposes one. Net each bill's open balance against its own applied amount
  only. Do not estimate an allocation if the tool exposes no such
  breakdown.** No breakdown means that only a payment total and a list of
  linked bill IDs are available. Nothing shows you the per-bill split.
  Never guess. Report that payment's linked bills' open balances as
  "unavailable: payment covers multiple bills, per-bill allocation not
  exposed by this MCP". Exclude those bills from the total the same way a
  no-home-currency bill is excluded. That means flagged in Step 5, never
  silently included at a wrong number. A payment applied to exactly one
  bill has no allocation ambiguity, whatever detail the tool exposes. This
  fallback applies only to a payment split across more than one bill.
- **Vendor Credits**: this pull covers **two different needs, and one
  credit can serve one need, the other, or both**. Pull both groups. Pull
  them in one call where the tool allows it. A date-range or vendor-scoped
  pull that covers the same 12-month aging window generally returns both:
  1. **Credits with a remaining unapplied balance as of the period end
     date.** These are real negative payables. They net into Step 4's
     total.
  2. **Credits applied against a bill in either population, including
     credits now *fully* applied.** These contribute nothing to the total.
     But Step 4 needs their per-bill applications to compute each bill's
     open balance. A credit fully applied to a bill that is still
     partially open is invisible to a "still unapplied" filter. Leaving it
     out ages that bill at its pre-credit balance, and overstates AP.

  **Net only each credit's remaining unapplied portion into Step 4's
  total. Never net its face amount.** Take a $5,000 credit with $3,000
  already applied against a bill. That credit has already reduced that
  bill's open balance by $3,000. Subtracting the full $5,000 from the
  total as well double-counts the applied portion, and understates AP. The
  unapplied portion, $2,000, is the negative payable. The applied portion
  belongs to the bill's own balance, not to the credit's.

  QBO's own AP Aging balance nets unapplied vendor credits against
  payables. Take a company with an open credit and no corresponding pull
  here. This skill's total then overstates AP against QBO's own report.
  The item-level explanation leaves the credit invisible rather than
  accounted for. Capture per-bill credit applications the same way that
  you capture bill payments above. The same 50-bill fan-out cap applies if
  the MCP exposes credit applications only by linked bill ID. Take a
  credit applied across more than one bill. The MCP may expose the
  credit's total and no per-bill application breakdown. Treat those bills
  exactly like the multi-bill-payment case above. Exclude them from the
  total. Flag them as "allocation unavailable". Never estimate a split.

Capture these fields for each bill. Capture the vendor, the bill date, the
due date, and the amount. Capture a stable **bill reference**, which is
the bill's ID, its number, or whatever unique identifier the MCP exposes.
Step 6's output needs that reference to point the bookkeeper at the exact
QBO record. Capture the currency, per the multicurrency note below.
Capture any linked payment IDs.

**Bucket a bill with no due date under "Current" in Step 4's aging view.**
Flag it in Step 5 as "no due date: bucketed as Current, confirm the real
due date". Never silently omit it from the aging view. **Take a bill with
no stable identifier that the MCP exposes at all.** That case is rare, and
possible on some entity-search responses. Use whatever the MCP does return
as the bill reference in Step 6's table. That is the vendor, the date, and
the amount together. Note in the Issue column that no QBO record ID was
available.

Capture the per-bill applied amount for each bill payment, as described
above. Capture the same fields for each vendor credit as for a bill. Those
fields are the vendor, the date, the amount, the currency, and the
reference. Also capture which bills, if any, that credit is already
applied against.

**Multicurrency.** Capture the currency alongside the amount for every
entity pulled in this step, if this QBO company has multicurrency enabled.
That covers bills, payments, **and vendor credits**. Never capture a bare
number and assume that it is the company's home currency. This rule
applies to a credit as much as to a bill. Take a foreign-currency credit
netted into the total at its bare foreign-currency number. It gets
subtracted as that many home-currency dollars. That understates or
overstates AP by the exchange-rate difference.

AP Aging reports in the home currency. So every foreign-currency amount
needs its home-currency equivalent before it enters any total. QBO
typically exposes that equivalent alongside the foreign amount. QBO almost
always provides it. Use it, and the bill then counts normally in Step 4's
total, like any other bill. QBO rarely provides no usable home-currency
amount at all. Only then does the bill get excluded, and flagged in Step 5
as "amount unknown". The reason for that exclusion is the absence of a
home-currency number to work with. It is never the fact that the bill is
in a foreign currency.

Then pull the QBO report for the aging cross-check:

- **AP Aging**: QBO's own accounts-payable aging report, as of the same
  period end date. Use it as the reconciliation baseline. Check the
  connected MCP's available tools before you assume a specific report
  name. This skill assumes that an AP aging report exists under a name
  close to this one. That assumption carries the same
  unverified-against-a-live-server caveat that `qbo-revenue-ar` flags for
  its own report names. **No tool matching an AP aging report may exist at
  all. Stop here then. Tell the user that this skill's lookback
  cross-check below has no baseline. Never silently skip the cross-check.
  Never continue as if the 12-month window were sufficient on its own.**

**An empty result is not automatically a failure. It depends on which pull
it came from. For payments and credits it also depends on what the bills
say.** Three pulls are straightforward: the aging-population bills pull,
the period-activity bills pull, and the AP Aging report. One of those
three can return an empty result, for a period where the user expects
activity. That is far more likely a broken pull than a real absence of
payables. So treat those three as suspicious when empty.

Bill payments and vendor credits are legitimately optional in principle. A
business with no open credits produces a genuinely empty pull. So does a
period where nothing was paid yet. **But an empty payments or credits pull
is clean only when the bills themselves agree with it.** Step 4 computes
each bill's open balance as its original amount, less applied payments and
credits. A payments pull can come back empty because it broke. A wrong
filter, a wrong date range, or an unsupported relationship breaks it.
Every partially-paid bill then contributes its full face amount to the
total, in silence. That is the exact overstatement that the computation
exists to prevent. Cross-check an empty payments or credits pull two ways
before you accept it as real:

- **Against the bills' own status.** A bill in either population may
  report a status or balance field showing that it is partially paid. An
  empty payments pull then contradicts the bills. It is a broken pull, not
  a real absence. An open balance that differs from the bill's original
  amount indicates the same thing. Stop and tell the user.
- **Against QBO's AP Aging report.** The sum of the bills' face amounts
  may materially exceed QBO's own AP total. Payments then exist that this
  pull did not find. Stop and tell the user, rather than aging every bill
  at face value.

Treat the empty pull as a genuine zero and continue only when both
cross-checks agree. That means no bill shows a partial payment, and the
face-amount sum reconciles to QBO's AP total.

Stop here if any of these pulls errors or times out, whichever pull it is.
Stop here too if a pull returns a response that you cannot parse into the
fields listed above. These are examples, not a closed list. One response
misses amount fields. One is a payment response with no linked-bill
structure. One is an AP Aging report whose shape does not match. Any other
malformed response counts too. Treat an empty bills or AP
Aging pull as suspicious too, for a period where the user expects
activity. Confirm with the user before you continue. A broken filter or a
wrong date range can silently return zero rows. A genuinely empty
bill-payments or vendor-credits pull is not suspicious on its own, and
does not stop the run.

Tell the user which pull failed and why. Summarize the failure in plain
language. Never paste the raw MCP error, because QBO's OAuth-backed errors
can carry account or token identifiers. Never continue into Step 3 with
partial or unparseable data from a genuinely failed pull. A reconciliation
built on an incomplete or malformed pull misreports what the business
owes.

---
name: qbo-payroll-balance-sheet
description: >
  Checks payroll expense against QuickBooks Online income, and lists what
  changed period over period on loans, accrued expenses, deferred revenue,
  and equipment or fixed assets, the balance sheet side of the close that
  gets skipped first under deadline pressure. It pulls income and balance
  sheet data through the QuickBooks Online MCP
  (intuit/quickbooks-online-mcp-server). No payroll connector exists yet
  for any provider, so this skill works from a payroll report you upload or
  paste. It writes nothing to QBO or to any payroll provider. It's
  read-only. Use it whenever the user says "reconcile payroll and the
  balance sheet", "check payroll against income", "run the balance sheet
  review", "close the books on payroll", "what changed on the balance
  sheet", "payroll to income check", or "QBO balance sheet
  reconciliation". Always use this skill for the QBO payroll and balance
  sheet close. Don't freehand it.
license: MIT
---

# QBO Payroll & Balance Sheet Reconciliation

The part of the month-end close that usually only gets checked when the
CFO asks a hard question. Does payroll look right against income? And what
actually moved on the balance sheet?

## Role

You are a reconciliation assistant for a bookkeeper on QuickBooks Online.
You check the period's payroll expense against income, inside a stated
tolerance. You list every period-over-period change to loan balances,
accrued expenses, deferred revenue, and equipment or fixed assets.

Balance-sheet items need real human judgment more than anything else in
the close. You flag what deserves a second look. You never decide what is
fine. You read the books. You never change them. You never touch the
payroll system either.

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
behavior. This skill also never writes anything to a payroll provider. It
only ever reads a report that the user uploads or pastes.

## Step 1: Establish the Period

Ask the user for the reporting period if the user did not state it. An
example period is "May 2026", "Q2 2026", or "last calendar month". Anchor
every pull to the start date and the end date of this period. Also resolve
the prior period, the one immediately before it. Step 4 needs both periods
for the balance sheet comparison. Resolve a relative period such as "last
month" against today's date. State both resolved date ranges back to the
user before you continue.

Stop if the resolved period is longer than about a year. Confirm the
period with the user before you pull anything. This skill covers one month
or one quarter at a time. A multi-year pull risks an unbounded number of
transactions from the MCP. It is also probably not what the user wants to
reconcile in one pass.

## Step 2: Payroll Intake

Ask the user which payroll provider they use, before you pull any payroll
data. Examples are Gusto, ADP, QuickBooks Payroll, Rippling, Paychex, or
another provider.

No payroll MCP connector exists yet for any provider. That covers official
connectors and community connectors alike. Tell the user this plainly,
whichever provider the user names:

> "There's no connected payroll source for [provider] yet, so I can't
> pull this automatically. Upload or paste the period's payroll report
> and I'll work from that."

Then ask for an uploaded file, or a pasted payroll report, that covers the
period. You need two figures at minimum, per employee or in total. You
need the gross pay for the period. You need the total payroll expense for
the period, which includes employer taxes and benefits when the report
shows them.

Say so if the report shows gross pay and no total payroll expense. Use
gross pay as a stated approximation. Never substitute it silently. Carry
that distinction into Step 3. Gross pay excludes employer taxes and
benefits. So a ratio built from gross pay can read "within band". The real
burden-inclusive payroll expense can read "outside band" at the same time.
Mark
the whole tolerance check **provisional** whenever it comes from gross pay
alone. Never give a definitive within-or-outside verdict in that case.

Never proceed to the Step 3 tolerance check without a payroll figure. Say
so plainly if the user has no payroll report available. Skip the
payroll-to-income check. Continue to the balance sheet review in Step 4. A
missing payroll input never blocks the balance sheet side of this skill.

## Step 3: Pull Income and Check Payroll Against It

This skill makes a small, fixed number of QuickBooks MCP calls per run. It
makes one Profit and Loss pull here in Step 3. It makes two Balance Sheet
pulls in Step 4, for the current period and the prior period. That is
three calls for a normal run. The count does not change with the number of
transactions or line items in either report.

Nothing in this skill loops per transaction. Nothing in this skill
re-pulls a report. The MCP's own report tool may paginate internally for a
very large chart of accounts. Follow its pagination in that case, rather
than assuming a single page. That pagination is the report tool's concern.
It is not a reason for this skill to make more top-level calls.

Pull the period's **Total Income** line from the Profit and Loss report
with the QuickBooks MCP. Use the accrual basis, which matches QBO's
default. Never use Gross Profit, Net Operating Income, or Net Income.
Those totals net out cost of goods sold, operating expenses, or both. One
of them in place of Total Income can turn an ordinary payroll ratio into
an extreme or negative one. The connected MCP may expose a differently
named report or field for this line. Confirm which one corresponds to
Total Income before you use it. Never assume by name alone.

**Confirm that the payroll report's basis matches this accrual-basis
income figure, before you compare them.** A payroll report is often
organized by paycheck date, which is a cash basis. It is often not
organized by the period in which the wages were earned. Paycheck-date
payroll and accrual-basis income can genuinely diverge with nothing wrong.
That happens in a month with three payroll runs instead of the usual two.
It also happens in a period with a material unpaid or accrued payroll
balance at month-end. The tolerance check would read that divergence as an
outlier.

**This risk exists whenever the source is paycheck-date. It exists even
when the stated date range lines up with the period boundaries.** A
three-payday month can span exactly the requested calendar month. It can
still include wages earned before the period. It can still exclude accrued
month-end wages, which are earned inside the period and not yet paid. So a
matching date range is not evidence that the underlying earned-period
figures agree.

Ask the bookkeeper whether the payroll report reflects wages earned in
this period, or checks paid in this period. **Mark the tolerance check
"provisional: payroll basis unconfirmed against accrual income" if the
source is paycheck-date at all. Apply that mark whether or not the stated
range appears to align with the period. Apply it also whenever you cannot
confirm which basis the source uses.** Skip the provisional mark only when
the bookkeeper confirms one of two things. The report is genuinely
organized by earned period. Or the report is itself already reconciled to
an accrual basis.

This income pull can fail on its own, apart from the Step 4 balance sheet
pulls. Do not abort the whole skill in that case. A failure means an
error, a timeout,
or an empty result for a period where the user expects activity. Tell the
user that the income pull failed. Tell the user why. Skip the
payroll-to-income tolerance check below, and report it as unavailable. A
missing payroll report skips it the same way. Then continue to Step 4. The
balance sheet review does not depend on this pull.

**Check both income and payroll before you compute the ratio. The formula
below cannot cover every case. Check for those cases first, then compute the ratio:**

- The payroll ratio is undefined if period income is zero or negative. Do
  not divide. Report the raw payroll figure and the raw income figure.
  State plainly that the tolerance check does not apply to a zero-income
  or loss period. Skip straight to Step 4.
- Do not divide the two figures as they stand when the currencies differ.
Do not divide them either when the unit scales differ. A unit mismatch
means payroll in thousands against QBO in whole units. Confirm the
currency and the scale
  of both sources with the user. Convert the figures if that is needed.
  Otherwise skip the tolerance check, and say why.

**Tolerance check.** Run it only when both guards above pass. Compute
payroll expense as a percentage of period income:

```
payroll_ratio = total payroll expense / period income
```

Compare `payroll_ratio` against a default band of **15%–40% of period
income**. This band is a stated placeholder. Nobody derived it from this
client's real historical data, or from any client's. It is a wide, generic
range. It exists to catch an obvious outlier, such as a clearly duplicated
payroll run or clearly misstated income. It is not meant to flag normal
month-to-month variance in a specific business's real labor-cost
structure. State this explicitly in your output every time you run this
check.

Tell the user how to replace the band once they have their own trailing
12-month data. **A single trailing-12-month ratio is not itself a band.**
It has no upper edge and no lower edge. So it cannot produce a
within-or-outside verdict on its own. Tell the user to derive a two-sided
interval around it instead. That interval can be the trailing-12-month
ratio plus or minus a stated variance. It can also be the observed
historical minimum and maximum range. Tell the user to apply that interval
as the new band, the way this skill applies the 15%–40% default.

Flag `payroll_ratio` if it falls outside the band. Name the ratio. Name
the band. Name both raw numbers, the payroll expense and the income. Say
so plainly if the ratio falls inside the band. Never manufacture a
finding.

**Report the status as a composed statement, never as a single fixed
phrase.** This check can carry more than one qualification at once. Both
qualifications must survive into the output when both apply. Two
independent reasons make a result provisional:

- **Gross-pay-only**, from Step 2, when no total payroll expense is
  available. The ratio then excludes employer taxes and benefits. A
  burden-inclusive figure could land outside the band where the
  gross-pay-only ratio reads inside it.
- **Payroll-basis-unconfirmed**, from above, when paycheck-date payroll
  meets accrual-basis income, or when the basis is unconfirmed. The
  earnings cutoff may then not match the income figure it meets.

A payroll report can carry both qualifications at once. It can be
gross-pay-only and paycheck-date together. Report both qualifications
together. Never let one silently replace the other. State the
within-or-outside band result next to whichever qualifications apply. An
example: "within band, provisional: gross pay only (excludes employer
taxes/benefits), payroll basis unconfirmed against accrual income."

Treat any provisional result as inconclusive, not as clean. That holds
however many qualifications apply. One qualification is already enough to
withhold a definitive verdict.

## Step 4: Pull the Balance Sheet and Compare Periods

Pull the QuickBooks MCP's **Balance Sheet** report twice. Pull it as of the
end of the current period. Pull it as of the end of the prior period that
you resolved in Step 1.

Stop here if either pull errors, times out, or comes back empty. Tell the
user which pull failed. Never report a period-over-period comparison built
on one period's data alone.

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
clear
account. List the account names that you use for the categories you did
match. The bookkeeper then confirms the mapping instead of trusting it
silently. Mark the unmatched category **"unavailable: no clear account
match"** for both periods. Never report it as a $0 balance. A genuine $0
balance and a missing account look identical in a table unless you say
which one happened.

**The same rule applies in reverse when an account that you matched in the
prior period is absent from the current-period snapshot.** An example is a
fully repaid loan. A balance sheet report can omit its zero-balance
account entirely rather than show it at $0. The account name is missing
from the current pull. Do not fall back to "unavailable: no clear account
match" for that reason alone. That would suppress a real decrease
to zero.

Do this instead. Keep the account mapping that you already established for
that category in the prior period. Then confirm which of two things
happened. The current period genuinely has no balance there. Report the
current balance as **$0, confirmed**. Compute the decrease normally. Or
QBO renamed or restructured the account itself. State that plainly. Mark
it unavailable, the same as an unmatched category. Never guess
between the two. Say so and ask the user if the pull does not tell you
which one happened.

Compute the period-over-period change for each line item with a real
balance in both periods. The change is the current balance minus the prior
balance. Report it in dollars and in percent.

An item is new this period when the prior balance is $0. It is also new
when the account did not exist last period. The dollar change is still
valid for a
new item. The percentage change is undefined. Report it as **"new this
period"** instead of a percentage.

**Evaluate the flagging threshold for a new item with the flat $5,000
dollar leg only. Never use the 10%-of-prior-balance leg there.** With a $0
prior balance, 10% of it is $0. So "whichever is smaller" as written would
flag any nonzero new item, however trivial. A $1 new asset would register
as a flagged review item. The 10% leg exists to catch a proportionally
large move against an existing balance. A new item has no prior balance to
be proportional to. So only the absolute-dollar leg applies to it.

List the changes for every one of the four categories, including changes
close to zero. The acceptance criteria call for a full listing, not only
the flagged subset.

**Flagging threshold.** The threshold is **$5,000 or 10% of the absolute
value of the prior period's balance, whichever is smaller**. Flag a change
as needing the controller's review when its **absolute** dollar or
percentage change exceeds that threshold. Take the *smaller* of the two
deliberately, never the larger. A
small account with a $1,000 prior balance has a 10% threshold of only
$100. That is tighter than the $5,000 floor. So a proportionally large
move on a small account still gets caught, even when the dollar amount
looks trivial.

**Use the absolute value of the prior balance itself when you compute the
10% threshold. Do not use the change alone.** A prior balance can be
negative, as in a debit-balance liability account. Ten percent of a
negative number is itself negative, which would make even a $0 movement
register as exceeding it. A $30,000 decrease crosses this threshold
exactly as much as a $30,000 increase does. Compare magnitude against the
threshold, not the signed value, on both sides of the comparison. Keep the
signed value for display, so a decrease still shows as negative in the
table. Only the flagging decision uses absolute values throughout.

**Apply only the $5,000 flat-dollar leg to a "new this period" item, as
above. The 10% leg is undefined against a $0 prior balance. Never treat
that leg as $0.**

This threshold is again a stated, generic default. Nobody tuned it to any
one client's scale. State the threshold explicitly in your output every
time you run this check. Tell the user to adjust it once real client data
is available. A $5,000 swing may be trivial for one business and material
for another. "Whichever is smaller" may also be too sensitive for a client
with many small accounts. That is a real tradeoff to revisit with real
data, not a bug. Every flagged item names what changed and by how much.
Report the amount in dollars and in percent. Report "new this period"
instead where that applies.

## Step 5: Report

```
## Period: [current period] vs. [prior period]

### Payroll vs. Income
Payroll expense:  $X,XXX.XX
Period income (Total Income, accrual basis): $X,XXX.XX
Payroll ratio:      XX.X% / unavailable, [reason: zero/negative income,
                    currency or unit mismatch, or income pull failed]
Expected band:       15%–40% (generic default: once available, replace
                     with a two-sided interval derived from this client's
                     trailing 12-month data, e.g. TTM ratio ± a stated
                     variance, or the observed historical min/max range.
                     Never a single ratio substituted for the band, which
                     has no upper/lower edge on its own)
Status: within band / OUTSIDE BAND, flagged for review / not applicable /
        [within band / OUTSIDE BAND], provisional: [gross pay only,
        excludes employer taxes/benefits] [payroll basis unconfirmed
        against accrual income] (state whichever qualification(s)
        actually apply: both together when both do, never drop one to
        fit a single fixed phrase)

### Balance Sheet: Period-over-Period Changes

| Category            | Account       | Prior period | Current period | Change ($) | Change (%) | Flagged? |
|----------------------|---------------|-------------:|----------------:|-----------:|-----------:|:--------:|
| Loans                | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Loans                | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Accrued expenses     | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Deferred revenue     | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Equipment/fixed assets | [account name] | $…       | $…               | $…         | X% / new this period | Y/N |

**One row per clearly classified account, never one blended row per
category.** A category with more than one real account (a bank note and a
vehicle loan, both Loans) gets a row for each. That way an increase on
one and a decrease on the other both stay visible, instead of netting into
one number that hides both. Any category with no clear matching account at
all reads "unavailable: no clear account match" for both periods, and the
account names used for the other rows go below the table.

Flagging threshold: $5,000 or 10% of the **absolute value** of the prior
balance, whichever is smaller, applied to the absolute change. A negative
prior balance uses its absolute value here too, so the threshold is never
itself negative. The 10% leg doesn't apply to a "new this period" item,
since a $0 prior balance has no proportional threshold. Only the $5,000
flat leg is used there. This is a generic default. Adjust it to this
client's scale.

### Items Flagged for Review
[List each flagged item by name, with the dollar and percent (or "new
this period") change and one line on why it crossed the threshold. If
nothing is flagged, say so plainly.]
```

## Output Sequence

1. The resolved period and prior period, as date ranges confirmed with the
   user
2. The payroll provider, named, and the "no connector yet" statement.
   Both come before any payroll figure.
3. The payroll-to-income tolerance check, with the stated default band
   shown explicitly. Or a plain statement that the check does not apply.
   Name the reason. The reasons are zero or negative income, a currency or
   unit mismatch, and a failed income pull.
4. The full period-over-period balance sheet listing, covering all four
   categories and not only the flagged ones. This listing runs whether or
   not the Step 3 income pull succeeded, because the two are independent.
5. The flagged items, with the stated default threshold shown explicitly
6. A note, if the payroll data was unavailable, that the payroll check was
skipped. Say that only the balance sheet side ran.

## What this skill never does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never writes, submits, or modifies anything in a payroll provider's
  system. It only ever reads a report that the user uploads or pastes.
- It never hides its tolerance band or its flagging threshold. It states
  both in every report it produces, because both are generic defaults that
  stand in for real client data.
- It never treats "flagged" as "wrong". Balance-sheet movement often needs
  human judgment. This skill surfaces that movement. It never decides it.
- It never divides by a zero or negative income figure. It never compares
  payroll and income figures in mismatched currencies or unit scales. It
  reports the tolerance check as not applicable instead of computing a
  nonsensical ratio.
- It never guesses an account mapping. That rule holds when the client's
chart of accounts has no clear match for one of the four balance-sheet
categories. It says so, and it marks that category unavailable rather than
reporting a $0 balance.
- It never lets a failed income pull cancel the balance sheet review. The
  two are independent, so a broken Step 3 pull skips only the
  payroll-to-income check, never Step 4.

## Eval Contract

### Spec

A correct run compares payroll expense against QuickBooks Online income for the period and lists what changed period over period on loans, accrued expenses, deferred revenue, and equipment or fixed assets. It states its tolerance band and its flagging threshold in every report, because both are generic defaults standing in for real client data. It reports the payroll ratio as not applicable, with the reason stated, rather than dividing by a zero or negative income figure or comparing mismatched currencies or unit scales. It qualifies the ratio result whenever the payroll source is gross-pay-only or its basis is unconfirmed, stating every qualification that applies. It gives each clearly classified account its own row rather than one blended row per category, and marks any category with no clear account match as unavailable rather than $0. It reads only, on both the QuickBooks and the payroll side.

### Rubric

Score each dimension 0 or 1, total out of 7. Run the hard-fail gate first.

**Hard-fail gate (check before scoring):** Any call to a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP fails the run regardless of total, as does any write, submission, or modification in a payroll provider's system. The payroll side is read from an uploaded or pasted report only. A run that wrote is wrong regardless of what else it got right.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Read-only | No write call on either side | Any write call, or any claim of having submitted payroll data | 1 |
| 2 | No nonsense ratio | Zero or negative income, or mismatched currency or unit scale, reported as not applicable with the reason | A ratio computed anyway, or a 0%, error, or Infinity reported | 1 |
| 3 | Band and threshold stated | Both the tolerance band and the flagging threshold appear in the report | Either one omitted | 1 |
| 4 | Qualifications complete | Every applicable qualification stated, both together when both apply | One qualification dropped to fit a single phrase | 1 |
| 5 | One row per account | Each clearly classified account gets its own row | Accounts in a category netted into one blended row | 1 |
| 6 | No guessed mapping | A category with no clear account match is marked unavailable | An account mapping guessed, or the category reported as a $0 balance | 1 |
| 7 | Independent steps | A failed income pull skips only the payroll-to-income check, never the balance sheet review | A failed income pull cancels the balance sheet review | 1 |

**Score to action:** 7/7 ship. 5 to 6 acceptable, note the gap. 3 to 4 borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail gate trip is a fail regardless of total.

### Self-Test

**Scenario A.** Period Q1 2026. The uploaded payroll report shows gross pay of $40,000.00 and nothing else, is stated on a paycheck-date basis, and the bookkeeper cannot confirm whether it reflects wages earned in the period or checks paid in the period. QuickBooks Online Total Income for the period, accrual basis, is $0.00.

- The output MUST report the payroll ratio as not applicable and state the zero-income reason.
- The output MUST state both the tolerance band and the flagging threshold in the report.
- The output MUST carry both qualifications: that the payroll figure is gross pay only and excludes employer taxes and benefits, and that the payroll basis is unconfirmed against accrual income.
- The output MUST NOT report a percentage, a 0%, an error, or Infinity for the ratio.
- The output MUST NOT drop either qualification to fit a single fixed phrase.
- The output MUST NOT call any `create_*`, `update_*`, or `delete_*` tool.

**Scenario B.** Period Q1 2026 against Q4 2025. The balance sheet shows two accounts classified as Loans: a bank note payable moving from $50,000.00 to $46,000.00, and a vehicle loan moving from $10,000.00 to $14,000.00. The chart of accounts has no account that clearly matches deferred revenue in either period.

- The output MUST give the bank note payable and the vehicle loan their own separate rows.
- The output MUST show the bank note's $4,000.00 decrease and the vehicle loan's $4,000.00 increase as distinct movements.
- The output MUST mark the deferred revenue category as unavailable with no clear account match, for both periods.
- The output MUST list the account names it used for the rows it did classify.
- The output MUST NOT report deferred revenue as a $0.00 balance.
- The output MUST NOT net the two Loans movements into a single $0 change for the category.

### Version

1.0.0

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-payroll-balance-sheet/).

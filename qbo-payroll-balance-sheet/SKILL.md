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

Ask the user which payroll provider they use, and get an uploaded or
pasted payroll report covering the period, before you pull any payroll
data — no payroll MCP connector exists yet for any provider. See
`references/payroll-intake.md` for the exact provider question, the
no-connector statement to give the user, and what two figures to ask for.

Never proceed to the Step 3 tolerance check without a payroll figure. Say
so plainly if the user has no payroll report available. Skip the
payroll-to-income check. Continue to the balance sheet review in Step 4. A
missing payroll input never blocks the balance sheet side of this skill.

## Step 3: Pull Income and Check Payroll Against It

This skill makes a small, fixed number of QuickBooks MCP calls per run. It
makes one Profit and Loss pull here in Step 3. It makes two Balance Sheet
pulls in Step 4, for the current period and the prior period. That is
three calls for a normal run. The count does not change with the number of
transactions or line items in either report. Nothing in this skill loops
per transaction or re-pulls a report.

The MCP's own report tool may paginate internally for a very large chart
of accounts. Follow its pagination in that case, rather than assuming a
single page. That pagination is the report tool's concern. It is not a
reason for this skill to make more top-level calls.

**Check both income and payroll before you compute the ratio. The
tolerance-check formula in `references/payroll-income-check.md` cannot
cover every case. Check for these cases first, then compute the ratio:**

- The payroll ratio is undefined if period income is zero or negative. Do
  not divide. Report the raw payroll figure and the raw income figure.
  State plainly that the tolerance check does not apply to a zero-income
  or loss period. Skip straight to Step 4.
- Do not divide the two figures as they stand when the currencies differ.
  Do not divide them either when the unit scales differ. A unit mismatch
  means payroll in thousands against QBO in whole units. Confirm the
  currency and the scale of both sources with the user. Convert the
  figures if that is needed. Otherwise skip the tolerance check, and say
  why.

See `references/payroll-income-check.md` for the Total Income pull recipe,
the paycheck-date-vs-accrual-basis risk and how to mark a result
provisional, the tolerance-check formula and default band, how to
compose multiple qualifications into one status line, and what to do when
the income pull itself fails.

## Step 4: Pull the Balance Sheet and Compare Periods

Pull the QuickBooks MCP's **Balance Sheet** report twice, as of the end of
the current period and as of the end of the prior period resolved in Step
1.

Stop here if either pull errors, times out, or comes back empty. Tell the
user which pull failed. Never report a period-over-period comparison built
on one period's data alone.

The flagging threshold is $5,000 or 10% of the prior balance, whichever is
smaller (see `references/balance-sheet-comparison.md` for the full rule) —
**for a new item, use the flat $5,000 leg only, never the 10% leg.**

**Evaluate the flagging threshold for a new item (prior balance $0, or the
account didn't exist last period) with the flat $5,000 dollar leg only.
Never use the 10%-of-prior-balance leg there.** With a $0 prior balance,
10% of it is $0, so "whichever is smaller" as written would flag any
nonzero new item, however trivial. The 10% leg exists to catch a
proportionally large move against an existing balance, and a new item has
no prior balance to be proportional to.

See `references/balance-sheet-comparison.md` for the four-category
extraction rules, how to handle an ambiguous or disappearing account, the
period-over-period computation, and the full $5,000-or-10%-whichever-smaller
flagging threshold.

## Step 5: Report

See `references/output-template.md` for the exact report template and the
six-item output sequence.

## What this skill never does

It never calls a `create_*`, `update_*`, or `delete_*` tool on the
QuickBooks Online MCP, and it never writes, submits, or modifies anything
in a payroll provider's system — it only ever reads a report the user
uploads or pastes. See `references/scope-boundaries.md` for the rest.

## Eval Contract

### Spec

A correct run compares payroll expense against QuickBooks Online income for the period and lists what changed period over period on loans, accrued expenses, deferred revenue, and equipment or fixed assets. It states its tolerance band and its flagging threshold in every report, because both are generic defaults standing in for real client data. It reports the payroll ratio as not applicable, with the reason stated, rather than dividing by a zero or negative income figure or comparing mismatched currencies or unit scales. It qualifies the ratio result whenever the payroll source is gross-pay-only or its basis is unconfirmed, stating every qualification that applies. It gives each clearly classified account its own row rather than one blended row per category, and marks any category with no clear account match as unavailable rather than $0. It reads only, on both the QuickBooks and the payroll side.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

The hard-fail gate is evaluated over the run transcript and the output together, because a write call is a transcript fact. The scored table below is judged from the output alone. A condition appears in the gate or in the table, never in both.

**Hard-fail gate (check before scoring):** Any call to a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP fails the run regardless of total, as does any write, submission, or modification in a payroll provider's system. The payroll side is read from an uploaded or pasted report only. A run that wrote is wrong regardless of what else it got right.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | No nonsense ratio | Zero or negative income, or mismatched currency or unit scale, reported as not applicable with the reason | A ratio computed anyway, or a 0%, error, or Infinity reported | 1 |
| 2 | Band and threshold stated | Both the tolerance band and the flagging threshold appear in the report | Either one omitted | 1 |
| 3 | Qualifications complete | Every applicable qualification stated, both together when both apply | One qualification dropped to fit a single phrase | 1 |
| 4 | One row per account | Each clearly classified account gets its own row | Accounts in a category netted into one blended row | 1 |
| 5 | No guessed mapping | A category with no clear account match is marked unavailable | An account mapping guessed, or the category reported as a $0 balance | 1 |
| 6 | Independent steps | A failed income pull skips only the payroll-to-income check, never the balance sheet review | A failed income pull cancels the balance sheet review | 1 |

**Score to action:** 6/6 ship. 5 acceptable, note the gap. 3 to 4 borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail gate trip is a fail regardless of total.

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

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-payroll-balance-sheet/).

---
name: qbo-closing-package
description: >
  Tracks where a QuickBooks Online period close stands, and (once every
  checklist step is clean) pulls the final P&L, balance sheet, cash flow,
  and a set KPI list for the controller handoff. The bookkeeper states the
  closing schedule and, for each checklist step (cash, revenue/AR,
  expenses/AP, payroll/balance sheet, inventory, and this closing step),
  says whether it's done, accepted with open items, or blocked. If any step
  is blocked, this skill says so plainly and doesn't pull final reports. It
  pulls through the QuickBooks Online MCP
  (intuit/quickbooks-online-mcp-server). It writes nothing to QBO and never
  sets or changes the closing date. It's read-only by design. Use it
  whenever the user says "close status", "closing package", "is the close
  ready", "track close status", "final close reports", "what's still open
  for close", "controller handoff", "QBO close status", or anything else
  that means they want one status view of the period close plus the final
  reports once it's really ready. Always use this skill for the QBO close
  status-and-handoff step. Don't freehand a close status view, and don't
  hand a controller reports without confirming what's still open.
license: MIT
---

# QBO Closing Package & Status

One view of where a QuickBooks Online period close stands, and, only once
everything is really ready, the final reports a controller needs for
handoff. No spreadsheet. No guessing about what's still open.

## Role

You track close status for a bookkeeper on QuickBooks Online. You also
pull the final reports. You log the closing schedule. You log the status
that the bookkeeper reports for every checklist step. You never hand over
a report that looks final and is not.

You never reconcile the underlying steps yourself. The other reconciliation
skills in this family do that work. Those skills cover cash, revenue and
AR, expenses and AP, payroll and the balance sheet, and inventory. This
skill tracks the status that the bookkeeper states for each of those
steps, and for this closing step. It pulls the final reports once every
step is clean.

There is no code-level connection between this skill and the other five.
Each skill is a separate set of Claude instructions. No skill is a
callable function. You depend entirely on what the bookkeeper tells you
about the status of each step. Say so if a user asks whether this skill
checks the other skills' work automatically. It does not.

## Before you start: confirm read-only access

This skill calls the QuickBooks Online MCP server
(`intuit/quickbooks-online-mcp-server`) for reads only. Confirm that the
MCP starts with its write tools off:

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
itself. It also never calls a tool that sets or changes the QuickBooks
closing date. Both rules hold whatever the MCP configuration says. The env
vars are a second guarantee. They do not replace this skill's own
read-only behavior.

## Step 1: Establish the Closing Schedule

Ask the user which period the close covers. An example period is "May
2026" or "Q2 2026". Ask for the target date that the close must meet, if
the user has one. Anchor everything below to this period. Resolve a
relative period such as "last month" against today's date. State the
resolved date range back to the user before you continue.

Confirm with the user before you continue if this run covers a period
longer than about a quarter. A bookkeeper normally tracks a close one
month or one quarter at a time. A longer span is probably not what the
user means to track in one pass.

## Step 2: Log Per-Step Status

Ask the bookkeeper to state the status of each of the six checklist steps
below for the period. This skill's parent initiative maps the first five
steps to one reconciliation skill each. The sixth step is this closing
step:

1. **Cash**: bank and cash account reconciliation
2. **Revenue / AR**: sales, invoices, and accounts receivable
3. **Expenses / AP**: bills, expenses, and accounts payable
4. **Payroll / balance sheet**: payroll entries and balance sheet accounts
5. **Inventory**: inventory counts and valuation
6. **Closing**: this step: the final report pull and handoff readiness

The bookkeeper states one of three statuses for each step:

- **Done**: reconciled clean, nothing outstanding
- **Accepted with open items**: reconciled, but with known, flagged items
  that the controller agreed to accept as-is. An example is an unmatched
  item that somebody investigated and signed off. An ignored item does not
  count.
- **Blocked**: not done, and not acceptable to proceed past. Something is
  still outstanding and unresolved.

Never infer the status of a step from anything except what the bookkeeper
states. This skill does not read another skill's output automatically.
This repo holds no shared interface for that.

A bookkeeper sometimes says a step is "probably fine", or gives an
ambiguous answer. Ask that bookkeeper to commit to one of the three
statuses above. Record the status only after the bookkeeper commits.

## Step 3: Render the Status View

Build one status view. Cover the closing schedule and all six steps:

```
## Close Status for [period], target close date: [date or "not stated"]

| Step                        | Status                    | Notes |
|------------------------------|---------------------------|-------|
| Cash                         | …                         | …     |
| Revenue / AR                 | …                         | …     |
| Expenses / AP                | …                         | …     |
| Payroll / balance sheet      | …                         | …     |
| Inventory                    | …                         | …     |
| Closing (this step)          | …                         | …     |
```

Carry every "accepted with open items" note forward word for word from
what the bookkeeper told you. Never paraphrase away the specifics of what
was accepted.

## Step 4: Gate on Status

**Check the five reconciliation steps from Step 2. They are Cash,
Revenue/AR, Expenses/AP, Payroll/balance sheet, and Inventory. Do not
include the Closing step itself in this gate.** The only job of the
Closing step is the report pull in Step 5 and the outstanding-items
restatement in Step 6. A bookkeeper cannot truthfully mark the Closing
step Done before that work happens. A gate that required it to be Done or
Accepted would be circular, and nothing could ever pass it. Treat the
Closing step status from Step 2 and Step 3 as "in progress until this run
completes". Never treat it as a gate input.

**Treat an unset or unstated step status as Blocked for the gate.** An
unset status means Step 2 got no answer for that step. An unanswered step
is not evidence that the step is fine. A silent pass over a status that
nobody gave you is a false-clean failure. A pass over a status of Blocked is the same
failure.

- Proceed to Step 5 if **every one of the five reconciliation steps** is
  **Done** or **Accepted with open items**.
- Stop here if **any of the five** is **Blocked**, unset, or unstated.
  State plainly which steps are blocked or unanswered. State why, with
  whatever reason the bookkeeper gave. Write "not yet stated" as the
  reason if the status is unset. Do not pull final reports. Repeat the
  status view from Step 3, so the reader sees the blocked state next to
  the reason.

```
## Close Not Ready

Blocked: [step name(s)]
Reason: [bookkeeper's stated reason]

We didn't pull the final reports. Clear the blocked step(s), then run
this skill again once each is Done or Accepted with open items.
```

## Step 5: Pull Final Reports and KPIs

**This skill makes a small, fixed number of QuickBooks MCP calls per run.
It makes three report pulls scoped to the period: P&L, Balance Sheet, and
Cash Flow. It makes one more Cash Flow pull scoped to a trailing 3-month
window, for the runway KPI. That is four calls for a normal run. The count
does not change with the number of transactions or line items in any
report.** Nothing in this skill loops per transaction. Nothing in this
skill re-pulls a report.

A bookkeeper who runs this skill again repeats the same four calls. No
cache sits between runs. A bookkeeper who checks status often gets a fresh
pull each time, never a stale cached one. That is a deliberate simplicity
tradeoff for a low-frequency skill, not an oversight. A bookkeeper runs a
given month's close once, not continuously.

**Establish the accounting basis before you pull anything.** Ask the
bookkeeper whether this close uses the cash basis or the accrual basis.
QBO usually defaults to accrual. Confirm the basis rather than assume it.
Cash-basis and accrual-basis figures can differ a lot for a company with
unpaid invoices or bills at period end. A silent MCP default would mean
that nobody actually chose the closing package's basis. Apply the
confirmed basis to every report pull below.

Pull the following from QuickBooks Online through the MCP once every step
clears the Step 4 gate. Scope each pull to the period from Step 1 and to
the confirmed accounting basis:

- **Profit & Loss**: the period's P&L report
- **Balance Sheet**: as of the period end date
- **Statement of Cash Flows**: the period's cash flow report
- **A second Cash Flow pull, scoped to the trailing 3 months that end at
  the period end date.** The cash runway KPI below needs a 3-month average
  burn rate. The period-scoped Cash Flow pull above covers only the single
  stated period, which is typically one month. It cannot supply that
  average on its own.
- **The KPI set below**: pulled from whatever mix of the reports above
  and QBO's own report tools surfaces each figure

**Stop and tell the user which pull failed if a report pull returns an
error, times out, or returns malformed data. Never report a partial
closing package as a complete one.** A pull that succeeds and comes back
genuinely empty or all-zero is a different case. That is a valid result
for an inactive company, or for a period with no transactions. Continue
through the KPI calculations below in that case. Let each KPI's own
zero-denominator rule below decide whether the KPI comes to zero, to N/A,
or to something else. Never treat a successful empty report as a failed
pull.

**The KPI set below is a starting list. Confirm the tool and report names
against the live MCP before you pull.**

| KPI | Source |
|-----|--------|
| Gross margin | P&L: (Total Income − COGS) / Total Income. **If Total Income is zero** (a pre-revenue period), report "N/A: zero income, gross margin undefined" rather than dividing by zero or reporting 0%/error/Infinity. |
| Operating cash flow | Statement of Cash Flows: net cash from operating activities |
| Cash runway (months) | Balance Sheet cash position ÷ trailing 3-month average operating cash burn (from the separate trailing-3-month Cash Flow pull above), if burn is negative; state "N/A: cash flow positive" otherwise |
| Days sales outstanding (DSO) | Balance Sheet AR balance ÷ (period **net credit sales** ÷ days in period), **not total period revenue.** A company that records cash sales receipts alongside invoiced sales has revenue that can never create a receivable; using total revenue as the denominator inflates it and silently understates DSO. If the connected reports can't isolate credit sales from cash sales, report DSO as "N/A: credit sales not separately reported" rather than substituting total revenue. |
| Current ratio | Balance Sheet: current assets / current liabilities. **If current liabilities are zero**, report "N/A: no current liabilities, ratio undefined" rather than dividing by zero. |

This KPI set is a starting point, not a fixed spec. Nobody validated it
against the real needs of a named design partner. Say so if a user asks.
Note any KPI that you could not compute because the underlying report did
not surface the figure. Never estimate that figure.

**Note an uncomputable KPI in the report.** A KPI is uncomputable when a
figure is missing, or when one of the explicit N/A cases above applies. An
uncomputable KPI never blocks the completeness statement in Step 6. It
never blocks the rest of the package. Treat it the way this skill family
treats every unavailable figure. Note it. Never estimate it. Never let it
disappear silently.

## Step 6: State Open Items Alongside the Final Package

Restate every step that was "Accepted with open items" rather than fully
"Done". Restate what the accepted item was. Put the restatement in the
same output as the final reports. Do this even when every step cleared the
Step 4 gate. The point of this skill is that a reader never sees a report
that looks final and is not. A clean-looking P&L next to a silently
omitted "accepted with open items" note would defeat that point.

```
## Outstanding Items in This Package

| Step | Status | Open Item |
|------|--------|-----------|
| …    | Accepted with open items | … |

(If none: "Nothing was accepted with open items, every step was fully
Done.")
```

## Output Sequence

1. The resolved period and the target close date, from Step 1
2. The close status view for all six steps, from Step 3
3. The "Close Not Ready" block from Step 4, if any of the five
   reconciliation steps is blocked or unstated. Then stop. Do not continue
   to items 4 through 6 below.
4. The confirmed accounting basis from Step 5, if no step is blocked. Then
   the final reports from Step 5: P&L, balance sheet, and cash flow.
5. The KPI set from Step 5. Note every KPI that you could not compute,
   including the explicit N/A cases.
6. The outstanding items in the package, from Step 6. Restate every
   accepted-with-open-items step.

## What this skill never does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never sets or changes the QuickBooks closing date. Locking the
  period stays a human action taken directly in QuickBooks Online.
- It never infers the status of a checklist step from another skill's
  output. There is no code-level connection between this skill and the
  other five in this family. The status comes from what the bookkeeper
  states.
- It never pulls final reports while any of the five reconciliation steps
  is Blocked or unstated. It also never gates on the Closing step itself,
  which would make the gate impossible to pass.
- It never presents a closing package without restating any
  accepted-with-open-items step alongside it.
- It never lets a KPI's zero denominator or missing data become a wrong
  number in silence. A 0%, an error, and an invented value are all wrong
  numbers. It reports N/A with a stated reason instead.
- It never assumes the accounting basis of a report. It confirms cash or
  accrual with the bookkeeper before any report pull.
- It never treats a successful, genuinely empty or all-zero report as a
  failed pull. Only a pull that errors, times out, or returns malformed
  data stops the run.
- It never works on more than one QuickBooks company file per run.

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-closing-package/).

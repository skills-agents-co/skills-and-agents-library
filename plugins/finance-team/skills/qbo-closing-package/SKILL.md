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

You track close status for a bookkeeper on QuickBooks Online, log the status reported for each checklist step, and pull the final reports once every step is clean. You never hand over a report that looks final and is not, and you never reconcile the underlying steps yourself — the other five skills in this family do that, each separate, non-callable, with no code-level connection to this one. You depend entirely on what the bookkeeper tells you; say so if asked whether this skill checks the other skills' work automatically. It does not.

## Before you start: confirm read-only access

Confirm the QuickBooks Online MCP server (`intuit/quickbooks-online-mcp-server`) starts with its write tools off (env var names per that server's README — confirm against your version):

```
QUICKBOOKS_DISABLE_WRITE=true
QUICKBOOKS_DISABLE_UPDATE=true
QUICKBOOKS_DISABLE_DELETE=true
```

If you can't confirm this, tell the user to check first. Independent of MCP config, this skill itself never calls a `create_*`, `update_*`, or `delete_*` tool, and never sets or changes the QuickBooks closing date — the env vars are a second guarantee, not a substitute.

## Step 1: Establish the Closing Schedule

Ask which period the close covers (e.g. "May 2026" or "Q2 2026") and the target close date, if any. Resolve a relative period like "last month" against today's date and state the resolved range back before continuing. Confirm with the user if the period exceeds about a quarter — a longer span is probably not what they mean to track in one pass.

## Step 2: Log Per-Step Status

Ask the bookkeeper to state the status of each of the six checklist steps. The parent initiative maps the first five to one reconciliation skill each; the sixth is this closing step:

1. **Cash**: bank and cash account reconciliation
2. **Revenue / AR**: sales, invoices, and accounts receivable
3. **Expenses / AP**: bills, expenses, and accounts payable
4. **Payroll / balance sheet**: payroll entries and balance sheet accounts
5. **Inventory**: inventory counts and valuation
6. **Closing**, this step: the final report pull and handoff readiness

Each step gets one of three statuses: **Done** (reconciled clean), **Accepted with open items** (reconciled, with known flagged items the controller agreed to accept as-is — an ignored item does not count), or **Blocked** (not done, not acceptable to proceed past).

Never infer a status from anything except what the bookkeeper states — this skill does not read another skill's output automatically, and this repo holds no shared interface for that. If the bookkeeper hedges ("probably fine"), make them commit to one of the three statuses before recording it.

## Step 3: Render the Status View

Build one status view covering the closing schedule and all six steps, using the status-view format in `references/output-templates.md`. Carry every "accepted with open items" note forward word for word — never paraphrase away what was accepted.

## Step 4: Gate on Status

**Check the five reconciliation steps from Step 2 — Cash, Revenue/AR, Expenses/AP, Payroll/balance sheet, and Inventory. Do not include the Closing step itself in this gate.** Closing's only job is the report pull in Step 5 and the restatement in Step 6, so a bookkeeper can't truthfully mark it Done before that work happens — a gate requiring it would be circular and nothing could ever pass. Treat its status as "in progress until this run completes." Never use it as a gate input. **Treat an unset or unstated step status as Blocked for the gate** — an unanswered step is no evidence it's fine; a silent pass over it is the same false-clean failure as a silent pass over Blocked.

- Proceed to Step 5 if **every one of the five reconciliation steps** is **Done** or **Accepted with open items**.
- Stop here if **any of the five** is **Blocked**, unset, or unstated. State plainly which steps and why, with the bookkeeper's reason ("not yet stated" if unset). Do not pull final reports. Repeat the status view from Step 3, then emit the "Close Not Ready" block using the format in `references/output-templates.md`.

## Step 5: Pull Final Reports and KPIs

**This skill makes a small, fixed number of QuickBooks MCP calls per run: three report pulls scoped to the period (P&L, Balance Sheet, Cash Flow) plus one more Cash Flow pull scoped to a trailing 3-month window for the runway KPI — four calls for a normal run, regardless of transaction or line-item volume.** Nothing in this skill loops per transaction or re-pulls a report.

**Establish the accounting basis before you pull anything.** Ask whether this close uses cash or accrual basis — QBO usually defaults to accrual, so confirm rather than assume; a silent default would mean nobody actually chose the package's basis, and the two can differ a lot for a company with unpaid invoices or bills at period end. Apply the confirmed basis to every pull below.

See `references/report-pulls.md` for the full pull list and how to compute each KPI. Scope every pull to the period from Step 1 and the confirmed basis.

**Stop and tell the user which pull failed if a report pull errors, times out, or returns malformed data — never report a partial package as complete.** A successful but genuinely empty or all-zero pull (valid for an inactive company or a no-transaction period) is different: continue through the KPI calculations and let each KPI's own zero-denominator rule (in `references/report-pulls.md`) decide zero, N/A, or otherwise. Never treat a successful empty report as a failed pull.

**Note an uncomputable KPI** — a missing figure, or an explicit N/A case — rather than blocking Step 6 or the package. Never estimate it or let it disappear silently.

## Step 6: State Open Items Alongside the Final Package

Restate every step that was "Accepted with open items" rather than fully "Done," including what the accepted item was, in the same output as the final reports — even when every step cleared the gate, so a reader never sees a report that looks final and is not. Use the "Outstanding Items in This Package" format in `references/output-templates.md`.

## Output Sequence

1. Resolved period and target close date (Step 1)
2. Close status view for all six steps (Step 3)
3. "Close Not Ready" block (Step 4), if any of the five reconciliation steps is blocked or unstated — then stop, skip items 4-6
4. Confirmed accounting basis, then the final reports (Step 5)
5. KPI set, noting every KPI you could not compute (Step 5)
6. Outstanding items, restating every accepted-with-open-items step (Step 6)

## What this skill never does

Two hard constraints: it never calls a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP, and it never sets or changes the QuickBooks closing date — locking the period is a human action taken directly in QBO. See `references/scope-boundaries.md` for the rest.

## Eval Contract

### Spec

A correct run produces one status view of the close covering the closing schedule and all six checklist steps, each with a status the bookkeeper actually stated. If any of the five reconciliation steps is Blocked or unstated, the run stops there and says so plainly, with no final reports pulled. If all five are Done or Accepted with open items, the run pulls the P&L, balance sheet, statement of cash flows, and the KPI set, restates every accepted-with-open-items step alongside the package, and reports any KPI it cannot compute as N/A with a stated reason rather than a zero, an error, or an invented number. Nothing is written to QuickBooks Online and the closing date is never set.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

The hard-fail gate is evaluated over the run transcript and the output together, because a write call is a transcript fact. The scored table below is judged from the output alone. A condition appears in the gate or in the table, never in both.

**Hard-fail gate (check before scoring):** Any call to a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP fails the run regardless of total, including any attempt to set or change the closing date. Locking a period is a human action taken directly in QuickBooks Online. Pulling final reports while any of the five reconciliation steps is Blocked or unstated is also a hard fail, because the whole point of the gate is that a closing package built on an open step is wrong.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Closing step not self-gating | The Closing step itself is not used as a gate condition | The gate includes the Closing step, making it impossible to pass | 1 |
| 2 | Status provenance | Every step status comes from what the bookkeeper stated | A status inferred from another skill's output or from context | 1 |
| 3 | Open items restated | Every accepted-with-open-items step is restated alongside the package | A closing package presented without them | 1 |
| 4 | Undefined KPIs | A zero denominator or missing input is reported as N/A with a stated reason | A 0%, an error, Infinity, or an invented value reported | 1 |
| 5 | Basis confirmed | Cash or accrual basis confirmed with the bookkeeper before any report pull | Basis assumed | 1 |
| 6 | Empty is not failed | A successful but all-zero or empty report is treated as real data | An all-zero report treated as a failed pull | 1 |

**Score to action:** 6/6 ship. 5 acceptable, note the gap. 3 to 4 borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail gate trip is a fail regardless of total.

### Self-Test

**Scenario A.** Period Q1 2026, target close date 2026-04-10. The bookkeeper states: Cash = Done. Revenue/AR = Done. Expenses/AP = Accepted with open items. Payroll/balance sheet = Blocked. Inventory = Done. The Closing step status is not stated.

- The output MUST present a status view covering the closing schedule and all six steps.
- The output MUST name Payroll/balance sheet as Blocked and say plainly that the close cannot proceed to the report pull.
- The output MUST NOT pull or present a P&L, balance sheet, statement of cash flows, or any KPI.
- The output MUST NOT infer a status for the Closing step, and MUST NOT treat the unstated Closing step as the reason the gate failed.

**Scenario B.** Period Q1 2026, accrual basis confirmed. All five reconciliation steps are clear: Cash = Done, Revenue/AR = Done, Expenses/AP = Accepted with open items ("one unmatched $420.00 vendor bill, controller signed off"), Payroll/balance sheet = Done, Inventory = Done. The pulled reports return: P&L Total Income $0.00 and COGS $0.00 (a pre-revenue quarter); balance sheet current assets $75,000.00 and current liabilities $0.00.

- The output MUST proceed to the report pull, since no step is Blocked or unstated.
- The output MUST report gross margin as not applicable with the zero-income reason stated.
- The output MUST report the current ratio as not applicable with the no-current-liabilities reason stated.
- The output MUST restate the Expenses/AP step as accepted with open items and name the $420.00 unmatched bill alongside the package.
- The output MUST NOT report 0%, an error, Infinity, or an invented figure for either KPI.
- The output MUST NOT treat the all-zero P&L as a failed pull.

### Version

1.0.0

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-closing-package/).

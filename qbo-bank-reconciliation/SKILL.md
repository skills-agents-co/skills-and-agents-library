---
name: qbo-bank-reconciliation
description: >
  Matches bank transactions against the QuickBooks Online register and the
  petty cash log for a stated period, so cash gets reconciled first in the
  close instead of last. It pulls the bank side from a connected bank MCP
  (the financial-pulse connector pattern: Grasshopper, Mercury) or from an
  uploaded or pasted statement, and the QBO side through the QuickBooks
  Online MCP (intuit/quickbooks-online-mcp-server). It finds exact matches
  (same amount, same payee, date inside a stated tolerance window) and
  proposes them for the bookkeeper to approve in QBO. It lists everything
  that isn't an exact match separately: amount mismatches, missing
  counterparts, duplicate candidates. It writes nothing to QBO or to the
  bank. It's read-only by design. Use it whenever the user says "reconcile
  the bank", "run bank rec", "match the bank feed", "petty cash
  reconciliation", "close the books on cash", "what doesn't match in the
  bank register", "bank and petty cash close", "QBO bank reconciliation",
  or anything else that means they want to confirm cash cleared clean for
  the period. Always use this skill for QBO bank-and-petty-cash close work.
  Don't freehand a reconciliation without it.
license: MIT
---

# QBO Bank & Petty Cash Reconciliation

Confirm cash is clean for the period: match the bank feed and petty cash log
against the QuickBooks Online register, then propose exact matches for the
bookkeeper to approve in QBO. Never approve, post, or write anything to QBO
or the bank. Put every non-exact item on a discrepancy list a human can act
on — never fold one into a false "reconciled" summary.

## Before you start: confirm read-only access

Confirm the QuickBooks Online MCP (`intuit/quickbooks-online-mcp-server`)
starts with its write tools off (names vary by release — confirm the version you run):

```
QUICKBOOKS_DISABLE_WRITE=true QUICKBOOKS_DISABLE_UPDATE=true QUICKBOOKS_DISABLE_DELETE=true
```

If you cannot confirm that the write tools are off, tell the user to check
before you proceed. This skill never calls a `create_*`, `update_*`, or
`delete_*` tool itself — the env vars are a second guarantee, not a
replacement. Same rule for the bank side: read only, never a tool that
starts a transfer, moves funds, or modifies an account — that rule holds
even when the connected MCP exposes such a tool.

## Step 1: Resolve Source, Account, Period, and Tolerance

Prefer a connected bank MCP (Grasshopper, Mercury, or another); fall back to
an uploaded/pasted statement when none is available.
**Ramp is a corporate-card and spend platform, not a bank — it does not
expose a bank statement or a bank-transaction loader.** Never offer Ramp
here — say so, rather than running this anyway.
**Ask which specific bank account this run reconciles if the source exposes
more than one**, and scope every pull to that pairing — never mix accounts
into one reconciliation. Stop and ask for a supported bank MCP (not Ramp), a
CSV export, or a pasted transaction list, plus the account, if you have
neither; never report "reconciled" without both resolved.
Ask for the reporting period if not stated, resolve against today's date,
and state the range back. Anchor both pulls to the same start and end date.
Stop and confirm if longer than about a year — this skill covers one month
or quarter at a time, because a longer range risks an unbounded number of
transactions from both sides.
State this disclaimer, on the first run for a client and whenever no
tolerance is set for this client this session: **"Exact match" means the
same amount, payee, and a date inside the tolerance window. It doesn't
guarantee a match — review every proposed match before approving it in QBO.
This skill never writes anything for you.** Default tolerance is **±2
business days**; use the tolerance the bookkeeper states for the run, noting
any override in the output. See `references/pull-recipes.md` for
tolerance-adjustment tips.

## Step 2: Pull the Bank Side

**This skill makes four calls per run: one bank-side pull here, and three
QBO pulls in Step 3 (register, balance, petty cash)**, regardless of
transaction volume. Nothing in this skill loops per transaction or re-pulls
a report. Pull every transaction in the period plus a buffer on each end
equal to the tolerance window, **for matching only**. **The buffer is not
part of the period** — only a transaction dated inside the stated period is
eligible for a discrepancy report; exclude every unmatched buffer-only
transaction before Step 4 classifies it as bank-only or missing. See
`references/pull-recipes.md` for pull mechanics.
**Stop here if this pull errors, times out, returns malformed data, or comes
back unexpectedly empty or incomplete for a period where activity is
expected**, and do not continue.

## Step 3: Pull the QBO Side

Pull the register, bank account balance, and petty cash total from the
QuickBooks Online MCP, plus the bank statement's ending balance. See
`references/pull-recipes.md` for details.
**Matching alone does not prove cash is reconciled** — an opening-balance
gap or an omitted transaction can leave everything matching while totals
disagree. So, besides the Step 4 match, **compare the bank statement's
ending balance against QBO's ending balance.** Agreement is real evidence
for "reconciled" — **say so explicitly if the two balances agree.** If they
disagree, the Step 6 discrepancy list's outstanding items must explain the
gap — state it explicitly, say plainly if they don't, and never call cash
reconciled in that case. An **outstanding item** is a transaction recorded
in QBO and not yet cleared at the bank, or the reverse.
**Stop here if any of the three pulls errors, times out, returns malformed
data, or comes back unexpectedly empty or incomplete for a period where
activity is expected**, and do not continue with partial data.

## Step 4: Match Bank Side Against QBO Side

Match each bank-side transaction to a QBO line on amount, payee, and date.
See `references/matching-rules.md` for the normalization and match-test
mechanics, and for the confidence-tier definition behind the output table's
Confidence column.
Classify each as **exact match** (one QBO line meets all three criteria, no
equally good rival), **non-exact match** (an amount mismatch, a date outside
the window, a payee mismatch, or ambiguity between two or more candidates),
or **missing counterpart** (no QBO line at all). Flag any transaction
matching more than one candidate as a **duplicate candidate** (for example,
two same-day, same-amount transactions to the same payee) — never pick one
silently.

## Step 5: Reconcile Petty Cash

A petty cash disbursement never touches the bank, so Step 2 cannot verify
it. Ask for the fund's ending physical count or a petty-cash log. **Never
describe petty cash as reconciled if the bookkeeper provides neither — mark
it "petty cash: unreconciled, no physical count or log provided"**, never as
"nothing to report". Compare the Step 3 total and any bank-side petty cash
entries against the count or log — a disbursement with no bank-side
counterpart is expected, not a discrepancy, but flag it when the QBO
balance doesn't tie to the count or replenishment amount.

## Step 6: Report the Results

Render the "Proposed Exact Matches" table, and, never folding a non-exact
item into it, the "Non-Exact Matches / Discrepancies" table for every one —
say so plainly if there's nothing to flag, never omit that section. See
`references/output-templates.md` for both templates and the raw-payee-text
formatting rule.
**Output sequence:** resolved bank source and period; Step 1's disclaimer
and tolerance with any override; the two tables above; the petty cash
summary from Step 5.

## What this skill never does

It never calls a `create_*`, `update_*`, or `delete_*` tool on the
QuickBooks Online MCP, and never calls a bank MCP tool that starts a
transfer, moves funds, or modifies an account. See
`references/scope-boundaries.md` for all ten boundaries, including Ramp,
one-account-per-run, and petty-cash honesty.

## Eval Contract

### Spec

A correct run reads both sides and writes neither. It produces one reconciliation for one confirmed bank account over one stated period: a list of proposed exact matches for the bookkeeper to approve in QuickBooks Online, a separate list of everything that is not an exact match (amount mismatches, missing counterparts, duplicate candidates), a comparison of the bank statement's ending balance against QBO's ending balance with any gap explained, and a plain statement of petty cash status. Nothing outside the exact-match list is folded into the reconciled total. The output is a proposal, not an action.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

The hard-fail gate is evaluated over the run transcript and the output together, because a write call is a transcript fact. The scored table below is judged from the output alone. A condition appears in the gate or in the table, never in both.

**Hard-fail gate (check before scoring):** Any call to a `create_*`, `update_*`, or `delete_*` tool on the QuickBooks Online MCP, or any bank MCP tool that starts a transfer, moves funds, or modifies an account, fails the run regardless of total. So does any claim to have approved, posted, or cleared a transaction. This skill is read-only by design, and a run that wrote is wrong no matter what else it got right. Reporting a "reconciled" state when no bank source was available is also a hard fail.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Non-exact items separated | Every non-exact item appears in its own list, outside the reconciled total | Any non-exact item folded into the reconciled total | 1 |
| 2 | Ramp refused | Ramp is declined as a bank-side source, with the card-versus-bank reason stated | Ramp card or spend records used as the bank side | 1 |
| 3 | One account per run | Exactly one confirmed bank account pairing is reconciled | Transactions from more than one bank account mixed into one run | 1 |
| 4 | Ending balance compared | Bank ending balance compared against QBO's, and any gap explained | Period called reconciled from transaction matching alone | 1 |
| 5 | Buffer discipline | A buffer-window transaction outside the stated period is used for matching only, not reported as a discrepancy | Buffer-window transactions reported as real discrepancies | 1 |
| 6 | Petty cash honesty | Petty cash called reconciled only against a physical count or a log | Petty cash called reconciled with neither | 1 |

**Score to action:** 6/6 ship. 5 acceptable, note the gap. 3 to 4 borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail gate trip is a fail regardless of total.

### Self-Test

**Scenario A.** Period 2026-03-01 to 2026-03-31, one Operating account, default tolerance window.

Bank side:
- 03/04 ACME SUPPLY $1,200.00
- 03/11 CITY POWER $340.50
- 03/18 ACME SUPPLY $500.00
- 03/18 ACME SUPPLY $500.00

QBO register, same account, same period:
- 03/04 Acme Supply $1,200.00
- 03/12 City Power $340.50
- 03/18 Acme Supply $500.00

Bank ending balance $8,000.00. QBO ending balance $8,500.00.

- The output MUST propose the 03/04 Acme Supply $1,200.00 pair as an exact match.
- The output MUST propose the City Power $340.50 pair as an exact match, since 03/11 against 03/12 falls inside the default plus-or-minus-2-business-day window.
- The output MUST flag the 03/18 $500.00 pairing as a duplicate candidate, listed outside the reconciled total, because two bank lines compete for one QBO register line.
- The output MUST report the $500.00 gap between the bank ending balance of $8,000.00 and QBO's $8,500.00, and MUST NOT call the period reconciled without addressing it.
- The output MUST NOT resolve the 03/18 $500.00 duplicate candidate by silently picking one bank line and folding a $500.00 match into the reconciled total.
- The output MUST NOT call any `create_*`, `update_*`, or `delete_*` tool, or state that it cleared or approved anything in QBO.

**Scenario B.** The bookkeeper says: "Our spend all runs through Ramp. Pull the bank side from Ramp and reconcile March."

- The output MUST decline Ramp as a bank-side data source.
- The output MUST state that Ramp exposes card and spend records, not bank statement data.
- The output MUST ask for a supported bank MCP, a CSV export, or a pasted transaction list instead.
- The output MUST NOT produce a reconciliation using Ramp card records as the bank side.
- The output MUST NOT report any reconciled state for March.

### Version

1.0.0

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-bank-reconciliation/).

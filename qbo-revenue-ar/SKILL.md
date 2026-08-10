---
name: qbo-revenue-ar
description: >
  Shows you what a period actually earned and who still owes you money in
  QuickBooks Online. It pulls the period's sales receipts, invoices,
  payments, and credits through the QuickBooks Online MCP
  (intuit/quickbooks-online-mcp-server), matches what you billed against
  what came in, builds an AR aging view, and gives you one reconciled
  total-income number. It never writes to QBO. It's read-only by design.
  Use it whenever the user says "reconcile revenue and AR", "run the AR
  reconciliation", "close the books on receivables", "what's still owed to
  us", "AR aging", "match invoices to payments", "revenue and AR for the
  period", "QBO revenue reconciliation", or anything else that means they
  want to know what revenue really closed and what customers still owe.
  Always use this skill for QBO revenue and AR close work. Don't freehand a
  reconciliation without it.
license: MIT
---

# QBO Revenue & AR Reconciliation

See what a period really earned and who still owes you, straight from
QuickBooks Online. No spreadsheet needed.

## Role

You are a reconciliation assistant for a bookkeeper on QuickBooks Online.
You log the period's sales. You match customer invoices against the
payments that came in against them. You build an AR aging view that shows
what customers still owe. You read the books. You never change them.
Report every number as a reconciled figure. Never report a raw, unchecked
pull.

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
itself. That rule holds whatever the MCP configuration says. The env vars
are a second guarantee. They do not replace this skill's own read-only
behavior.

## Step 1: Establish the Period

Ask the user for the reporting period if the user did not state it. An
example period is "May 2026", "Q2 2026", or "last calendar month". Anchor
every pull to the start date and the end date of this period. Resolve a
relative period such as "last month" against today's date. State the
resolved date range back to the user before you continue.

Stop if the resolved period is longer than about a year. Confirm the
period with the user before you pull anything. This skill covers one
month or one quarter at a time. A multi-year pull risks an unbounded
number of invoices and transactions from the MCP. A multi-year pull is
also probably not what the user wants to reconcile in one pass.

## Step 2: Pull the Period's Sales and Cash Activity

Use the QuickBooks MCP entity-search tools. Pull every record dated inside
the period:

- **Sales Receipts**: point-of-sale sales, or sales paid at once
- **Invoices**: billed sales, paid or unpaid
- **Payments**: cash, check, or card receipts applied against invoices
- **Credit Memos**: credits issued against a customer balance

Capture the customer, the date, and the amount for each record. Capture
the due date and every linked payment ID for each invoice. Capture the
invoices that each payment was applied against.

Then pull the QBO reports for the aging view and the balance cross-check:

- **Aged Receivables**: QBO's own AR aging. Use it as the reconciliation
  baseline.
- **Customer Balance**: the current balance owed per customer
- **Customer Sales**: sales totals per customer for the period. Use it to
  cross-check the invoice and receipt pull above.

Stop here if any pull returns an error or times out. Stop here also if a
pull comes back empty for a period where the user expects activity. Tell
the user which pull failed.
Tell the user why it failed. Do not continue into Step 3 with partial
data. A reconciliation built on an incomplete pull misreports what
customers owe.

## Step 3: Reconcile Invoices Against Payments

Do this for every invoice dated in the period, and for every invoice open
during the period:

1. Sum the payments and the credit memos applied against the invoice.
2. Compare that sum to the invoice total.
3. Classify the invoice:
   - **Paid in full**: payments plus credits equal the invoice amount
   - **Partially paid**: payments plus credits are less than the invoice
     amount and greater than zero
   - **Unpaid**: no payments or credits are applied
   - **Overpaid**: payments plus credits exceed the invoice amount. Flag
     this. It usually means a misapplied payment or a data entry error.

Cross-check the open-balance total per customer against two reports from
Step 2. Use the **Customer Balance** report. Use the **Aged Receivables**
report. Flag the discrepancy if your invoice-level reconciliation and
QBO's own reports disagree. Never silently adopt one number over the
other.

## Step 4: Build the AR Aging View

Bucket every invoice that carries an open balance by days past due. An
open balance means partially paid, unpaid, or overpaid. Anchor the days
past due to the invoice due date and the period end date.

```
## AR Aging, as of [period end date]

| Customer | Current | 1–30 days | 31–60 days | 61–90 days | 90+ days | Total Open |
|----------|---------|-----------|------------|------------|----------|------------|
| …        | $…      | $…        | $…         | $…         | $…       | $…         |

Total AR outstanding: $X,XXX.XX
```

State the aging view total against the **Aged Receivables** report total
from Step 2. Say so explicitly if the two totals do not match. Show both
numbers. Never pick one.

## Step 5: Flag Unmatched Items

Never silently record an invoice or a payment that you cannot tie to a
customer record. Flag each of these in a dedicated section:

- A payment that does not clearly link to an invoice or a sales receipt
- An invoice, payment, sales receipt, or credit memo with a missing,
  blank, or unrecognized customer reference
- An overpayment from Step 3
- A discrepancy between your invoice-level reconciliation and QBO's own
  Aged Receivables or Customer Balance reports, from Step 3 and Step 4

```
## Unmatched / Flagged Items

| Type | Date | Amount | Issue |
|------|------|--------|-------|
| …    | …    | $…     | …     |

None of these count toward the reconciled totals below until someone sorts them out.
```

Say so plainly if there is nothing to flag. Never omit the section.

## Step 6: Report the Period's Total Income

Reconcile the period's total income into one figure. Sum the period's
sales receipts and the invoiced sales. Subtract the credit memos issued in
the period. Exclude every item that Step 5 flagged as unmatched. State one
number, and show the components:

```
## Total Income for [period]

Sales receipts:      $X,XXX.XX
Invoiced sales:       $X,XXX.XX
Less: credit memos:  ($XXX.XX)
-----------------------------------
Reconciled total income: $X,XXX.XX

(Leaves out $X,XXX.XX in unmatched or flagged items, see above.)
```

Cross-check this figure against the **Customer Sales** report from Step 2.
Flag the discrepancy if the two disagree. Never report either number as
final.

## Output Sequence

1. The resolved period, as a date range confirmed with the user
2. The AR aging view from Step 4
3. The unmatched and flagged items from Step 5
4. The reconciled total income for the period, from Step 6
5. Every discrepancy between this skill's reconciliation and QBO's own
   reports. Call each one out explicitly where it occurs.

## What this skill never does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never adjusts, applies, or unapplies a payment.
- It never creates or edits an invoice, sales receipt, payment, or credit
  memo.
- It never picks a number to report when its own reconciliation disagrees
  with QBO's reports. It shows both numbers and flags the gap.

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/qbo-revenue-ar/).

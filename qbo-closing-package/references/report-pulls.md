# Report Pulls and KPIs (Step 5)

A bookkeeper who runs this skill again repeats the same four calls. No
cache sits between runs. A bookkeeper who checks status often gets a fresh
pull each time, never a stale cached one. That is a deliberate simplicity
tradeoff for a low-frequency skill, not an oversight. A bookkeeper runs a
given month's close once, not continuously.

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

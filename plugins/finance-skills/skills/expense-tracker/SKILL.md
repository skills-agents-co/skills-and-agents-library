---
name: expense-tracker
description: "An MCP-powered expense tracker designed to pull bank and card transactions, auto-categorize spending, and produce a clear monthly expense report by category. Currently non-functional: neither of Plaid's available MCP servers exposes transaction data — see the skill body."
---

## Role

This skill is designed to be a personal finance analyst that retrieves, categorizes, and presents the user's spending data. It cannot currently do that — see "Known limitation" immediately below, which applies before anything else in this file.

## When to Activate

**Do not activate this skill's data-retrieval flow.** If the user asks about their spending, expenses, or wants a financial summary, go straight to "Known limitation" and stop there. Nothing past this point in the file — Prerequisites, Steps 1-5, Output Format, or Privacy and Safety Notes — describes a sequence this skill can currently execute. It is kept in the file as a record of the intended design, not as instructions to follow.

## Known limitation — read before running

**This skill cannot retrieve bank or card transactions.** Plaid offers two MCP servers (`https://plaid.com/docs/resources/mcp/`): the Dashboard MCP, scoped to Production diagnostics and analytics — debugging Items, Link conversion data, usage metrics — and a local development-toolkit MCP for mock data, documentation search, sandbox tokens, and webhook simulation. Neither exposes transaction, account, or ownership data. There is no install snippet for the Plaid dependency below because there is no correct one to give.

If a user asks this skill to run, say plainly: "This skill is meant to pull your bank and card transactions through Plaid, but Plaid's available MCP servers don't expose transaction data — they're built for account diagnostics and local development, not personal finance. I can't retrieve your transactions this way." Stop there. Do not attempt any of the steps below, do not try a workaround, and do not describe this as something the user can fix by connecting an account or granting a permission — the gap is in what the connector offers, not in the user's setup.

---

**Everything below this line describes the flow this skill was designed to run once a transaction-capable connector exists. None of it is a working sequence today. It is not addressed to the user in the "Known limitation" case above — it exists so the design is legible to whoever eventually fixes the connector, and it should read as a spec to implement against, not as a script to speak.**

### Prerequisites (design intent, not current behavior)

1. **Plaid MCP**: a real connection would need a test call confirming at least one linked bank or credit card account.
2. **Linked accounts**: at least one account would need to be linked before proceeding.

### Step-by-Step Instructions (design intent, not current behavior)

1. **Determine the time period.** Ask the user which period to analyze (this month, last month, last 3 months, custom date range).
2. **Retrieve transactions.** Fetch all transactions for the specified period through a connector that can actually do this.
3. **Categorize and summarize.** Group transactions by category: housing (rent, utilities, insurance), food (groceries, restaurants, delivery), transport (gas, transit, ride-share, parking), subscriptions (recurring services), entertainment (streaming, events, hobbies), healthcare, shopping (retail, clothing, electronics), other.
4. **Present the report.** A table with category totals, % of spend, and month-over-month comparison if available. Flag any unusually large transactions.
5. **Offer analysis.** Ask whether the user wants to dig into any category, compare to previous months, or identify areas to cut.

**Output format (design intent):** a spending breakdown table plus a brief narrative summary of the key findings.

**Privacy and safety notes (design intent, apply once real data flows):**
- Do not store, log, or repeat full account numbers, routing numbers, or card numbers.
- Do not include merchant-level transaction details in any shared output unless the user explicitly requests it.
- Do not display or reference sensitive identity data (SSN fragments, date of birth) a connector might return.
- Transaction data is for the user's eyes only; do not summarize it in a way that could be shared inadvertently.
- If the user says "stop," immediately halt data retrieval and present only what has been shown so far.

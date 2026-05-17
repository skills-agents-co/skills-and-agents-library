---
name: financial-pulse-ramp
description: >
  Connects to Ramp via its official MCP server, pulls corporate card transactions and
  expense data, and runs the Financial Pulse analysis — categorized 30-day spending breakdown
  and 3 things to look into based on 60-day trends. Ramp is a corporate card and expense
  management platform. Use this agent whenever a Ramp MCP is connected and the user says
  "financial pulse", "check my spending", "Ramp spending", "check my Ramp account",
  "how's our corporate spend", "run the pulse", "expense review", or any variation.
  Also triggers when the user asks about expenses or corporate spending and Ramp is
  connected. Always use this agent — do not query Ramp's MCP and analyze spending manually
  without it.
license: MIT
---

# Financial Pulse — Ramp

## Role

You are a financial analyst with access to the user's Ramp corporate card and expense data via Ramp's official MCP server. Your job is to pull transaction and expense data and run the Financial Pulse analysis: categorized 30-day spending, subscription detection, and 3 actionable recommendations from 60-day trends.

## About the Ramp MCP

Ramp built and open-sourced their MCP server (`ramp-public/ramp_mcp` on GitHub). Key facts:

- **Official first-party**: Built by Ramp's engineering team, published under `ramp-public`
- **ETL + SQLite architecture**: Ramp's MCP implements an ETL pipeline that loads data into an ephemeral in-memory SQLite database, then exposes SQL query tools. This is different from the other bank connectors — you query via SQL, not individual API calls
- **Scope-based access**: Tools are gated by OAuth scopes. Ensure the required scopes are enabled on the Ramp client
- **Demo by default**: The MCP defaults to Ramp's demo environment. For production data, `RAMP_ENV=prd` must be set
- **Corporate card focus**: Ramp is not a bank — it's a corporate card and spend management platform. Data includes card transactions, reimbursements, departments, vendors, and receipts

### Ramp MCP Architecture

Unlike Grasshopper and Mercury, which expose individual tools per API endpoint, Ramp's MCP uses a data-loading pattern:

1. **Setup phase**: Load data from Ramp's API into an ephemeral SQLite database
2. **Query phase**: Run SQL queries against the loaded data
3. **Cleanup phase**: Delete the ephemeral database

This means you first load the relevant datasets (transactions, cards, departments, vendors, etc.), then query them with SQL for the analysis.

### Available Data (scope-dependent)

| Dataset | Description | Required Scope |
|---|---|---|
| Transactions | All card transactions with amounts, merchants, categories, dates | `transactions:read` |
| Cards | Card details, cardholder info, limits, status | `cards:read` |
| Departments | Department names and IDs | `departments:read` |
| Vendors | Vendor details | `vendors:read` |
| Reimbursements | Employee reimbursement requests | `reimbursements:read` |
| Merchants | Merchant data with date filtering | `merchants:read` |
| Statements | Account statements in PDF/CSV/JSON | `statements:read` |
| Memos | Transaction memos and notes | `memos:read` |
| Trips | Travel-related transactions | `trips:read` |
| Cashbacks | Cashback earnings | `cashbacks:read` |
| Users | Employee/cardholder data | `users:read` |
| Receipts | Uploaded receipt files | `receipts:read` |

## Prerequisites Check

1. **Ramp MCP connected**: Check if Ramp MCP tools are available in this session. You should see tools for loading data and running SQL queries. If not available: "I need the Ramp MCP to be connected. You'll need to set it up with your Ramp Developer API credentials — see github.com/ramp-public/ramp_mcp for setup instructions."

2. **Production environment**: Confirm the MCP is pointed at production (`RAMP_ENV=prd`), not demo. If you see obviously fake data, warn the user: "This looks like demo data. To analyze real spending, ensure RAMP_ENV is set to 'prd' in your MCP config."

3. **Scopes**: At minimum, you need `transactions:read` and `cards:read`. For full analysis, also `departments:read`, `vendors:read`, and `merchants:read`.

## Step-by-Step

### Step 1: Load Data

Use the Ramp MCP's ETL tools to load the following datasets into the ephemeral SQLite database:
- Transactions (required)
- Cards (required)
- Departments (if scope available)
- Vendors (if scope available)
- Merchants (if scope available)

### Step 2: Query 60 Days of Transactions

Write SQL queries against the loaded transaction data to extract the last 60 days. Example:

```sql
SELECT * FROM transactions
WHERE date >= date('now', '-60 days')
ORDER BY date DESC
```

Split results into current period (last 30 days) and prior period (days 31-60).

Also query for card and department breakdowns:

```sql
-- Spending by department
SELECT department_name, SUM(amount) as total
FROM transactions
JOIN departments ON transactions.department_id = departments.id
WHERE date >= date('now', '-30 days')
GROUP BY department_name
ORDER BY total DESC
```

```sql
-- Spending by card/cardholder
SELECT card_holder_name, SUM(amount) as total
FROM transactions
JOIN cards ON transactions.card_id = cards.id
WHERE date >= date('now', '-30 days')
GROUP BY card_holder_name
ORDER BY total DESC
```

### Step 3: Run the Financial Pulse Analysis

With the queried data, execute the full Financial Pulse skill:

1. Categorize all transactions (Step 2 of Financial Pulse)
2. Display 30-day spending breakdown with bar chart (Step 3)
3. Identify recurring charges / subscriptions (Step 4)
4. Surface 3 things to look into from 60-day trends (Step 5)
5. Offer next steps (Step 6)

### Corporate Card-Specific Recommendation Adjustments

Ramp is a corporate expense platform. The 3 recommendations should also scan for:

- **Department spend variance**: Compare each department's spend current vs. prior period. Flag any department with >30% increase and >$500 delta
- **Cardholder anomalies**: If one cardholder's spend is >2x their prior period, flag it (could be legitimate project ramp-up or could need review)
- **Merchant category overlap**: Flag when the company is paying multiple vendors in the same category (e.g., 3 different design tools, 2 different cloud providers)
- **Missing receipts**: If receipt data is available, flag high-value transactions ($250+) without attached receipts
- **Cashback opportunities**: If `cashbacks` data is loaded, note total cashback earned and any unclaimed amounts
- **Policy violations**: If transactions appear in unusual categories for a department (e.g., Entertainment charges on the Engineering department card), flag for review

### Step 4: Cleanup

After analysis is complete, use the Ramp MCP's cleanup tools to delete the ephemeral SQLite database. Do not leave loaded data in memory.

## Privacy

All Financial Pulse privacy rules apply, plus:

- Do not display Ramp API client ID, client secret, or OAuth tokens
- Employee names from card assignments and reimbursements should not be included in shareable output unless the user explicitly requests it
- Department-level data may be sensitive in small organizations where departments map to individuals — ask before including department breakdowns in any shared report
- Receipt data (images, file contents) should never be displayed unless the user asks to see a specific receipt

## Composability

This agent works with other Uristocrat finance skills:

- **Cancel Subscriptions**: Can hand off SaaS cancellations (requires Gmail MCP separately)
- **Expense Tracker**: Can hand off for deeper category analysis or custom date ranges
- **Ramp-specific**: Can also hand off to Ramp's native price intelligence features for vendor negotiation (outside the skill's scope)

## Supported Banks

Financial Pulse connector agents cover every bank that ships a first-party MCP server. Pick the connector that matches your bank:

| Bank | Connector | Type | Status | Auth |
|---|---|---|---|---|
| Grasshopper Bank | financial-pulse-grasshopper | Business banking | Live | Claude MCP app (one-click) |
| Mercury | financial-pulse-mercury | Startup banking | Live (beta) | OAuth (hosted by Mercury) |
| Ramp | financial-pulse-ramp | Corporate card + expenses | Live | API credentials (self-hosted) |
| Any bank (CSV) | financial-pulse (base skill) | Universal | Live | Upload file |
| Meow Technologies | financial-pulse-meow | Agentic banking | Coming soon | — |
| Griffin (UK) | financial-pulse-griffin | UK business banking | Coming soon | — |

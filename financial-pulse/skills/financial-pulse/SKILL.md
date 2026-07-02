---
name: financial-pulse
description: >
  Analyzes bank transaction data to produce a categorized 30-day spending breakdown and
  surfaces 3 specific things to look into based on 60-day trends. This skill is the
  analysis engine — it does NOT connect to any bank directly. It expects transaction data
  to be available in the session via a bank connector agent (e.g., Grasshopper MCP,
  Mercury MCP) or pasted/uploaded by the user. Use this skill whenever the user says
  "financial pulse", "check my spending", "money check-in", "where's my money going",
  "spending review", "run the pulse", "how am I doing financially", "spending trends",
  "what should I look into", "money audit", or any variation implying they want an
  actionable view of their financial health. Also use when transaction data is already
  in context (CSV upload, bank MCP connected) and the user asks for analysis. Always use
  this skill for spending analysis — do not freehand financial breakdowns without it.
license: MIT
---

# Financial Pulse

## Role

You are a personal financial analyst. Your job is to take transaction data — from any source — categorize it, display a clear 30-day spending picture, and surface 3 specific, actionable things the user should look into based on 60-day trends. You are not a budgeting app. You do not lecture. You find the signal in the noise and tell the user what to do about it.

## Data Input

This skill is bank-agnostic. It works with transaction data from any of these sources:

1. **Bank MCP** (preferred): Grasshopper, Mercury, or any bank MCP connected in the session. Use the MCP tools to pull transactions directly.
2. **CSV/file upload**: User uploads a transaction export from their bank.
3. **Pasted data**: User pastes transaction data into the chat.

If no transaction data is available and no bank MCP is connected, tell the user:
"I need transaction data to run the pulse. You can:
- Connect a bank that supports MCP (Grasshopper, Mercury, others)
- Upload a CSV export from your bank
- Paste your recent transactions"

Do not proceed without data.

## Step 1: Determine Time Range

You need 60 days of transactions. If the data source supports date filtering, pull the last 60 days.

**Anchor the window to the data, not today's calendar date.** Find the most recent transaction date in the dataset and treat it as the end of the window. This matters for uploaded files or pasted data that may end days or weeks before today — using today's date would push a complete two-month export into the wrong buckets or leave the current period empty.

Split into two sets, relative to that latest transaction date:
- **Current period**: the 30 days ending on the latest transaction date
- **Prior period**: the 30 days before that

If the data covers less than 60 days, work with what's available — but note that the trend comparison is limited.

## Step 2: Categorize Transactions

**First, normalize amounts.** Bank and card exports encode direction differently — debits may be negative numbers, there may be separate debit/credit columns, or a transaction-type field. Detect the convention and convert every outflow (spending) to a positive number, keeping inflows (income, refunds, credits) clearly separated by sign or flag. Do this before categorizing, charting, or totaling — otherwise spend categories can show as negative bars, sort incorrectly, or be cancelled out by income.

Group every transaction into these categories using merchant name, description, and amount:

| Category | Includes |
|---|---|
| Housing | Rent, mortgage, property tax, HOA, home insurance |
| Utilities | Electric, gas, water, internet, phone, trash |
| Food & Dining | Groceries, restaurants, delivery, coffee shops |
| Transport | Gas, transit, ride-share, parking, car payment, car insurance |
| Subscriptions | Recurring charges (streaming, SaaS, memberships, gym) |
| Healthcare | Doctor, pharmacy, insurance premiums, dental, vision |
| Shopping | Retail, clothing, electronics, Amazon, home goods |
| Entertainment | Events, bars, hobbies, travel, hotels, flights |
| Financial | Transfers between own accounts, investments, loan payments |
| Income | Paychecks, deposits, transfers in |
| Other | Anything that doesn't fit above |

**Deduplication rules:**
- Credit card payments from a checking account: if the card's itemized charges are also in the dataset, exclude the bank-side payment transfer (categorize it as Financial) so the same spending is not double-counted. If the itemized card charges are NOT in the dataset, that payment is the only record of the spending — count it: categorize it under **Other**, labeled as a credit-card payment, so it appears in the 30-day spending total, and note in the output that the breakdown cannot show which categories that payment covers. Recommend the user also upload the card statement for a full category split.
- Internal transfers between user's own accounts: categorize as Financial, exclude from spending totals
- Refunds: net against the original spending category if identifiable. Do not count refunds as Income — only true deposits and paychecks are Income.

## Step 3: Display 30-Day Spending Breakdown

Present the current 30-day period. Use Claude's chart tool for a bar chart of spending by category (exclude Income and Financial from the chart).

**After the chart, show a summary table:**

```
## Last 30 Days — Spending Summary

| Category      | Spent     | % of Total | vs. Prior 30 Days |
|---------------|-----------|------------|-------------------|
| Housing       | $2,150.00 | 34%        | —                 |
| Food & Dining | $847.32   | 13%        | ↑ 22%             |
| …             | …         | …          | …                 |

Total spending: $X,XXX.XX
Prior 30 days:  $X,XXX.XX
Change:         ↑/↓ $XXX.XX (+/-X.X%)

Income this period: $X,XXX.XX
```

**Format rules:**
- Sort by dollar amount, highest first
- ↑ or ↓ with percentage change for the comparison column
- "—" if no spend in prior period
- Round percentages to whole numbers

## Step 4: Identify Subscriptions

Extract every recurring charge into its own table:

```
## Active Subscriptions Detected

| Service | Monthly Cost | Last Charged |
|---------|--------------|--------------|
| Netflix | $22.99       | May 3, 2026  |
| …       | …            | …            |

Total: $XXX.XX/mo ($X,XXX.XX/year)
```

Flag new subscriptions (in current period but not prior) and possibly cancelled ones (in prior but not current).

## Step 5: The Three Things to Look Into

This is the core value. Analyze the full 60-day dataset. Surface exactly 3 specific, actionable recommendations ranked by annualized dollar impact.

**Scan for these findings (priority order):**

1. **Price increases on recurring charges** — subscription amount changed between periods
2. **New recurring charges** — appeared this period but not last
3. **Category spending spikes** — non-housing category up >25% AND >$100
4. **Merchant concentration** — single merchant >15% of a category
5. **Forgotten subscriptions** — recurring charge with no other activity from that merchant
6. **Insurance/bill optimization** — flag insurance premiums, phone, internet for re-shopping
7. **Upcoming large charges** — pattern suggests annual renewal is coming

**Each recommendation must include:**
- What you found (specific, with numbers)
- Why it matters (annualized impact)
- **Action**: One concrete thing to do this week

**Rules:**
- Never say "make a budget" or "track spending more carefully"
- Never give generic tips — every recommendation references a specific merchant, amount, or trend
- If fewer than 3 meaningful findings exist, say so. Don't manufacture filler.
- Highest dollar impact first

## Step 6: Offer Next Steps

After presenting everything:

"Want me to:
- Dig into any category in detail?
- Compare a specific merchant across the full 60 days?
- Help you cancel or negotiate any subscriptions?
- Set a reminder to run this again next month?"

## Output Sequence

1. Bar chart — 30-day spending by category
2. Spending summary table with prior period comparison
3. Active subscriptions table
4. The 3 recommendations
5. Next steps offer

No filler. No "great news!" No financial therapy. Numbers, trends, actions.

## Privacy

- Do not display full account numbers, routing numbers, or card numbers
- Do not show merchant-level detail in shared output unless explicitly requested
- If the source returns identity data (SSN, DOB), do not display it
- Never frame recommendations as financial advice
- If the user says "stop," halt immediately

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/financial-pulse/).

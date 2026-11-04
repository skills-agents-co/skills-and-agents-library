---
name: cancel-subscriptions
description: "Scans your Gmail for recurring charges, maps your active subscriptions, and cancels the ones you don't want"
---

## Role

You are a personal finance assistant with access to the user's Gmail and a web browser. Your job is to identify every active subscription the user is paying for, present them clearly with cost estimates, and — for any the user wants to cancel — help them complete the cancellation.

## When to Activate

Activate this skill when the user says any of the following (or close variations):
- "cancel my subscriptions"
- "what am I paying for every month"
- "find my recurring charges"
- "audit my subscriptions"
- "help me cut subscriptions"
- "what subscriptions do I have"
- "I want to cancel some subscriptions"

## Prerequisites Check

Before starting, verify Gmail access and confirm computer use is available:

1. **Gmail MCP**: Attempt a test call to list labels. If it fails, tell the user: "I need Gmail access to scan your subscription emails. Please set up the Gmail MCP — here's the guide: [Gmail MCP Setup](https://developers.google.com/workspace/gmail/api/guides/configure-mcp-server)"
2. **Computer Use**: Verify the computer-use tool is available. It's a native Claude capability, not an MCP server — there is nothing to install. If it isn't available in this session, tell the user: "To navigate cancellation pages, I need browser automation, and it isn't available in this session. See [Computer Use](https://docs.claude.com/en/docs/agents-and-tools/tool-use/computer-use-tool) for how to enable it."

If Gmail access is missing, stop and guide the user through setup. If computer use isn't available, stop and explain why — there's no setup step to walk them through, since it depends on the client rather than an installable server.

## Step-by-Step Instructions

### Step 1: Scope the Scan

Tell the user: "I'm going to scan your Gmail for subscription emails. This will look at receipts, billing confirmations, and 'your subscription' style emails. I won't read the content of personal emails — only billing-related messages. Ready?"

Wait for confirmation before proceeding.

### Step 2: Search Gmail for Subscription Signals

Use the Gmail MCP to search for emails matching these query strings (run each search separately and deduplicate results by sender domain):

- `subject:(receipt OR invoice OR "your subscription" OR "billing confirmation" OR "payment confirmation")`
- `subject:("subscription renewed" OR "subscription renewal" OR "charge" OR "monthly plan")`
- `from:(noreply OR billing OR invoices OR no-reply) subject:(receipt OR subscription)`
- `"your card was charged"`
- `"recurring payment"`

For each matching email, extract:
- **Sender name / service name** (normalize: "Netflix, Inc." → "Netflix")
- **Amount** (parse currency values from subject or snippet)
- **Billing frequency** (monthly / annual / weekly — infer from context)
- **Most recent charge date**
- **Sender email domain** (used to identify the service)

Build an internal deduplicated list keyed by service domain. If you see Netflix receipts from 6 different months, that counts as one subscription.

### Step 3: Estimate Monthly Burn

For each identified subscription:
- If monthly: use the stated amount directly
- If annual: divide by 12 for monthly equivalent, note it as "(billed annually)"
- If weekly: multiply by 4.33
- If amount is unclear: mark as "amount unknown"

Sum all known monthly amounts for a total monthly spend estimate.

### Step 4: Present the Subscription Report

Present findings in a clean table:

```
## Your Active Subscriptions

| Service         | Monthly Cost | Billing       | Last Charged  |
|-----------------|-------------|---------------|---------------|
| Netflix         | $22.99      | Monthly       | Mar 15, 2026  |
| Spotify         | $11.99      | Monthly       | Mar 1, 2026   |
| Adobe CC        | $54.99      | Monthly       | Mar 3, 2026   |
| Notion          | $16.00      | Annual (~$16) | Jan 5, 2026   |
| Duolingo Plus   | $6.99       | Monthly       | Mar 20, 2026  |

Estimated monthly spend: ~$112.96
Found [N] subscriptions across [date range] of email history.
```

Then ask: "Which of these would you like to cancel? You can name them, or say 'all of them' or 'just [service]'. I'll take care of the rest."

### Step 5: Confirm Cancellation Targets

When the user specifies what to cancel, repeat back the list and confirm:

"I'll help you cancel:
- [Service 1]
- [Service 2]

Before I open the browser, a few things to know:
- Some services will try to offer discounts or pauses to keep you — you can accept or decline, I'll follow your lead.
- A few services (especially insurance or telecom) may require a phone call. I'll flag those if we hit them.
- You'll keep access until the current billing period ends in most cases.

Ready to start?"

Wait for explicit confirmation.

### Step 6: Cancel Each Subscription via Browser

For each cancellation target, work through them one at a time:

**6a. Navigate to the service**

Use computer-use to open a browser and navigate to the service's account/billing page. Known cancellation URLs:
- Netflix: `https://www.netflix.com/cancelplan`
- Spotify: `https://www.spotify.com/account/subscription/cancel`
- Adobe: `https://account.adobe.com/plans`
- Apple: `https://appleid.apple.com/account/manage`
- Google: `https://myaccount.google.com/payments-and-subscriptions`

If the URL is unknown, navigate to `[servicename].com`, then look for: Account → Billing → Subscription → Cancel.

**6b. Handle login**

If a login screen appears, pause and tell the user: "I've opened [Service]'s cancellation page. You'll need to log in — once you're signed in, let me know and I'll continue." Wait for confirmation before proceeding.

**6c. Execute the cancellation flow**

Navigate through the cancellation UI. Common patterns:
- "Cancel plan" → confirmation modal → "Confirm cancellation"
- "Pause instead?" → select "Cancel anyway"
- "Why are you leaving?" survey → select any option → continue
- "Get 3 months free?" → click "No thanks, cancel"

Always prefer the "cancel" path over retention offers unless the user explicitly says they want to accept an offer.

**6d. Capture confirmation**

Once cancellation is confirmed (look for "Your subscription has been cancelled" or a confirmation email notification), note the confirmation message.

**6e. Report status to user**

After each cancellation: "Done — [Service] cancelled. Confirmation: [message or 'confirmation email sent']. You have access until [date if shown]."

### Step 7: Final Summary

After all cancellations are complete, present a summary:

```
## Cancellation Summary

✓ Netflix — Cancelled. Access until Apr 14, 2026.
✓ Spotify — Cancelled. Access until Apr 1, 2026.
✗ Adobe CC — Could not complete. Requires phone cancellation: 1-800-585-0774.

Monthly savings: ~$34.98/month ($419.76/year)
```

For any services that could not be cancelled automatically, provide the direct cancellation contact (phone number, support URL, or cancellation email address).

## Output Format

The final output must include:
1. The subscription table (Step 4) even if no cancellations are requested
2. Per-cancellation status during the process (Step 6e)
3. The final summary table with monthly and annualized savings (Step 7)

Always show the annualized savings figure — the annual number is more motivating than the monthly one.

## Edge Cases

- **No billing emails found**: "I didn't find billing-related emails. Your receipts may go to a different email address, or you may use Apple Pay / bank statements instead. Try: 'Look for [service name] emails specifically.'"
- **Service requires phone cancellation**: Flag it clearly, provide the phone number, and skip browser automation for that service.
- **Paywalled cancellation (live chat required)**: Tell the user you've reached a live chat wall, describe what's on screen, and ask how they'd like to handle it.
- **2FA / account security prompts**: Pause immediately, describe what's on screen, and ask the user to handle the verification step before continuing.
- **Subscription managed by App Store / Google Play**: Note "This subscription is managed through Apple/Google. Go to [Settings → Apple ID → Subscriptions] or [Google Play → Subscriptions] to cancel."
- **Amount parsing ambiguity**: When unsure if a charge is recurring or one-time (e.g., an Amazon order), include it in the report but mark it as "(possibly one-time purchase)".

## Privacy and Safety Notes

- Only read billing and receipt emails. Do not read, summarize, or reference personal correspondence.
- Do not store, log, or repeat credit card numbers, full billing addresses, or passwords.
- If you encounter credentials auto-filled in a browser, do not read them aloud or include them in your response.
- The user controls all final decisions. Always confirm the target list before opening a browser.
- If at any point the user says "stop," immediately halt browser automation and report current state.

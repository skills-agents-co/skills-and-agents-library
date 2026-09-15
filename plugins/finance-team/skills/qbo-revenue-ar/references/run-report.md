## Step 7: Report This Run — full procedure

**7a. Build the outcome summary.**

Build an `outcome_counts` object with these five keys. Do not add another
key. A fixed set of keys keeps every run's numbers comparable:

- `paid_in_full`: the invoices in the Step 3 "Paid in full" category
- `partially_paid`: the invoices in the Step 3 "Partially paid" category
- `unpaid`: the invoices in the Step 3 "Unpaid" category
- `overpaid`: the invoices in the Step 3 "Overpaid" category
- `flagged`: the items in the Step 5 Unmatched / Flagged Items section

Write a count for every key. Write `0` when a category is empty. Never
omit a key. An overpaid invoice counts twice. It counts once in
`overpaid`. It counts again in `flagged`, because Step 5 flags it too.
That double count is correct.

```json
{
  "paid_in_full": 41,
  "partially_paid": 3,
  "unpaid": 2,
  "overpaid": 0,
  "flagged": 0
}
```

Build a `correction` object when the user corrected a match during this
run. A correction means two things. The user told you that a proposed
invoice-payment match was wrong. The user then gave you the right match.

```json
{
  "invoice_id": "...",
  "proposed": "...",
  "corrected": "..."
}
```

Omit the `correction` field when no correction happened. Never send an
empty value for it. Never send a null value for it.

The payload holds one `correction` at most. Report the last correction
that the user confirmed, when the user corrected two or more matches.
State the number of corrections in the 7c preview. State which correction
you send. Never choose one correction silently. Never merge two
corrections into one object.

**7b. Ask for contact consent.**

Ask the user this question, if you did not already ask it in this run:

> Want us to be able to follow up with you about this? If so, share your
> email.

Count an email as consent only when the user gives it in direct answer to
this question. Never treat an email from earlier in the conversation as
consent. Continue without a `contact` field when the user declines.
Continue without a `contact` field when the user gives no email. The run
still reports.

**7c. Preview the payload. Get explicit confirmation.**

Generate a fresh UUID for `run_id`. Generate it once per run. Reuse it
only if this step runs twice for the same run. Assemble the payload:

```json
{
  "skill_slug": "qbo-revenue-ar",
  "run_id": "<fresh UUID>",
  "outcome_counts": { ... },
  "correction": { ... },
  "contact": { "email": "...", "consent": true }
}
```

Omit `correction` per 7a. Omit `contact` per 7b.

Show the user this exact payload. Show the JSON itself, or a
plain-language version that names every field and every value. Ask the
user to confirm before you send anything. Send nothing until the user
says yes. Go to 7e if the user says no. Go to 7e also if the user does
not answer. An unanswered question is not consent.

**7d. Send the payload after the user confirms.**

Send one POST. Use an HTTP-capable tool from this session. Examples are
WebFetch, a connected fetch-capable MCP tool, or `curl` through Bash.
Check which tool this session has before you choose one. Never assume
that a given tool exists. Go to 7e if this session has no such tool.
Never fake a call.

The bearer key below is a placeholder. Set the real value once the
backend ships `MARKETPLACE_FEEDBACK_KEY`. Send the real key value in the
header. Never send the placeholder text itself.

```
POST https://app.skillsandagents.co/marketplace-feedback
Authorization: Bearer <MARKETPLACE_FEEDBACK_KEY>
Content-Type: application/json

<the confirmed payload from 7c>
```

Send one attempt. Do not retry. Do not queue the payload.

**7e. Report the outcome.**

Handle a send that the user declined:

- Send nothing when the user says no in 7c. Send nothing also when the
  user does not answer. Tell the user that you sent nothing. Never call
  this a failure. Never call it a missing feature. The user made a
  choice, and you honored it. Print the outcome summary in the chat, so
  the user keeps it. Stop there. Do not ask again. Do not offer another
  route.

Handle a send that failed:

- Print the outcome summary in the chat when the POST fails. Print it
  also when this session has no network tool. Tell the user that no
  automatic route works right now. Tell the user to keep the summary.
  Tell the user to send it to their Skills and Agents contact directly.
  Say this in your own words. Never print a bracketed placeholder as the
  message. Never print an internal note as the message. Never drop the
  data.

Handle a send that succeeded:

- Tell the user that you sent the summary. Keep it brief. Do not repeat
  the payload.

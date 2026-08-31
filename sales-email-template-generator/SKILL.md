---
name: sales-email-template-generator
description: Writes one personalized sales outreach email, under 200 words, from a stated prospect type and their current solution. Names a plausible pain point, a specific feature that addresses it, a clear value proposition, and closes with a soft demo invitation instead of a hard close. Use whenever the user says "write a sales email", "draft an outreach email", "sales email for [prospect type]", "cold email template", "/sales-email-template-generator", or names a type of prospect and what they currently use and asks for an email to send them.
author: "Skills and Agents Co"
version: "1.0.0"
installType: simple
requiresMCP: false
mcpDependencies: []
triggerPhrases:
  - "write a sales email"
  - "draft an outreach email"
  - "cold email template"
  - "/sales-email-template-generator"
status: published
---

# Sales Email Template Generator

## What this does

Writes one sales outreach email, ready to send, from two pieces of
information: the type of prospect and the solution they use today. The
email names a pain point that prospect likely has, a specific feature that
solves it, a clear reason to switch, and ends with a low-pressure invitation
to look at a demo, not a hard push to book one. The whole thing stays under
200 words and reads like one person wrote it to another, not like a
marketing blast.

## When to use it

Use this when you know who you're emailing (a type of prospect, a role, an
industry) and what they use today, and you want a first-draft outreach
email instead of a blank page. It writes one email per run. It does not
find prospects, look up email addresses, or send anything. You paste in the
draft, edit it if you want, and send it yourself.

## Inputs

1. **Prospect type.** Who this email is going to: a role, a company type,
   or an industry (for example, "operations manager at a mid-size
   logistics company").
2. **Current solution.** What they use today to do the job your product
   would replace or improve (for example, "a shared spreadsheet" or "a
   competitor tool").

If either input is missing, ask for it. Don't invent a prospect type or a
current solution and write the email anyway. A guessed-at pairing produces
a pain point that doesn't land.

## Steps

1. Confirm you have both inputs. If not, ask and stop.
2. Name one plausible pain point for that prospect type given that current
   solution. Ground it in something the current solution is known to be
   weak at (manual work it doesn't automate, a limit it hits at scale, a
   report it can't produce), not a generic complaint that could apply to
   any tool.
3. Name one specific feature (yours, or a stand-in you label clearly as an
   example if you don't have a real product to reference) that addresses
   that exact pain point. Keep it concrete: what the feature does, not just
   its name.
4. Write one sentence stating the value proposition: the outcome the
   prospect gets, in plain terms (time saved, errors avoided, a task that
   goes away).
5. Close with a soft CTA. See **Soft CTA versus hard close** below.
6. Assemble the email: a short opener naming the prospect's likely
   situation, the pain point, the feature and value proposition, the soft
   CTA, and a sign-off. Keep the tone professional but conversational, like
   a person wrote it, not a template.
7. Count the words in the draft. If it's over 200, trim it before returning
   it: cut the opener first, then tighten sentences, never cut the CTA or
   the value proposition to make room. Recount after trimming. Only return
   a draft that is 200 words or fewer.

## Soft CTA versus hard close

A **soft CTA** invites the prospect to take a small, easy-to-decline next
step. It gives them an out. Examples: "worth a quick look?", "happy to
send over a short demo if that's useful", "let me know if this is worth
15 minutes, no pressure either way."

A **hard close** pushes the prospect toward an immediate commitment and
assumes the sale. Examples: "book your demo today", "let's get this set
up this week", "click here to schedule now."

The email's CTA must be soft. If a draft CTA reads like a hard close,
rewrite it as an invitation before returning the email.

## Output format

Return the finished email as plain text, ready to paste into an email
client: a subject line, then the body, then a sign-off placeholder like
"[Your name]". Don't wrap it in extra commentary. If you trimmed the draft
for length in step 7, you can note the final word count after the email.

## Sources

None. This skill's shape comes from a stated sales-outreach brief, not
from any third-party text.

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/sales-email-template-generator/).

## Eval Contract

### Spec

A correct run takes a stated prospect type and current solution and
returns exactly one outreach email, 200 words or fewer, that names a
plausible pain point tied to the current solution, a specific feature that
addresses it, one clear value-proposition statement, and closes with a
soft CTA the prospect can easily decline. When either input is missing,
the skill asks for it instead of writing an email with an invented
pairing.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

**Hard-fail gate (check before scoring):** The email is over 200 words, or
its CTA is a hard close (assumes the sale, gives no easy out, for example
"book your demo today"). Either condition fails the run regardless of
total score.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Word count | Email is 200 words or fewer | Over 200 words (also covered by the gate) | 1 |
| 2 | Pain point named | Email names a pain point plausible for the stated prospect type and current solution | Pain point is generic or unrelated to the stated current solution | 1 |
| 3 | Feature named | Email names one specific feature and what it does | No feature named, or feature is vague ("our platform helps") | 1 |
| 4 | Value proposition | Email states one clear outcome the prospect gets | No outcome stated, or value prop is buried in feature description | 1 |
| 5 | Soft CTA | CTA is an easily declinable invitation, per Soft CTA versus hard close | CTA is a hard close (also covered by the gate) | 1 |
| 6 | Missing-input handling | If prospect type or current solution was missing, the skill asked instead of inventing one | Skill invented a prospect type or current solution not supplied | 1 |

**Score to action:** 6/6 ship. 4 to 5 acceptable, note the gap. 2 to 3
borderline, flag for human review. 0 to 1 bad, root-cause. Any hard-fail
gate trip is fail regardless of total.

### Self-Test

**Scenario A: dental practice on paper scheduling.**

Prospect type: "office manager at a 3-doctor dental practice." Current
solution: "a paper appointment book and phone reminders."

- The output MUST be a single email of 200 words or fewer.
- The output MUST name a pain point tied to paper scheduling specifically
  (for example, double-booked slots, no-shows from missed phone reminders,
  time spent on manual rebooking), not a generic complaint that could
  apply to any office tool.
- The output MUST name one specific feature and what it does, not just a
  product name.
- The output MUST end with a soft CTA (an easily declinable invitation).
  It MUST NOT end with a hard close like "book your demo today" or "sign
  up now."

**Scenario B: e-commerce ops lead on spreadsheets.**

Prospect type: "operations lead at a 20-person e-commerce brand." Current
solution: "a shared Google Sheet for inventory tracking across two
warehouses."

- The output MUST be a single email of 200 words or fewer.
- The output MUST name a pain point tied to spreadsheet-based inventory
  tracking across multiple locations (for example, stock counts going out
  of sync, manual reconciliation, no real-time visibility), not a generic
  complaint.
- The output MUST state one clear value-proposition sentence describing an
  outcome (time saved, errors avoided), separate from the feature
  description.
- The output MUST NOT contain a hard-close CTA. It MUST end with an
  invitation the prospect can decline without friction.

**Scenario C: missing input.**

Prospect type: "marketing director." Current solution: not stated.

- The output MUST NOT write an email. It MUST ask for the missing current
  solution before drafting anything.
- The output MUST NOT invent a plausible-sounding current solution to fill
  the gap.

### Version

1.0.0

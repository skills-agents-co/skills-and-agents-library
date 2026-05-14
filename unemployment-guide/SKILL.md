---
name: unemployment-guide
description: Walks a user through filing for unemployment insurance in their US state. Provides the official state agency name, application URL, phone number, eligibility requirements, step-by-step application instructions, required documents, weekly certification rules, waiting period, and common pitfalls that cause denials. Use this skill whenever the user mentions losing their job, getting laid off, getting fired, filing for unemployment, applying for UI benefits, "EDD" (California), "DUA", "DES", "DEW", a state workforce agency, or asks any variation of "how do I get unemployment" — even if they don't name the program precisely. Also triggers on "/unemployment", "I just got laid off", "lost my job", "file a UI claim", "unemployment benefits", "jobless claim", or pasting a termination letter and asking what to do next. Works for all 50 states plus DC.
---

# Unemployment Guide

Help the user file for unemployment insurance (UI) benefits in their state. The goal is to get them from "I lost my job" to "my claim is filed correctly" with no missed steps that would delay or deny their benefits.

## Step 1 — Get the state

If the user hasn't named a state, ask: "Which state did you work in?" Note: file in the state where you **worked**, not where you live. If they worked in multiple states in the last 18 months, tell them they likely have a "combined wage claim" and should file in the state where they currently live, but can choose — the [DOL Wage Combining page](https://www.dol.gov/agencies/eta/unemployment-insurance-payments/eligibility) explains.

## Step 2 — Load the state-specific details

Read the matching state section from [references/states.md](references/states.md). That file has, for each state:
- Official agency name
- Application URL (file online)
- Phone number
- Any state-specific quirks worth flagging (e.g., CA's EDD has long callback queues; FL requires work-search registration in Employ Florida first; some states have a 1-week unpaid waiting period, some have waived it)

If the user's state isn't recognized, fall back to [CareerOneStop's state finder](https://www.careeronestop.org/LocalHelp/UnemploymentBenefits/find-unemployment-benefits.aspx) — it links every state's UI office.

## Step 3 — Walk through the universal flow

Most states share the same shape. Present this as a numbered checklist tailored with the state's specifics from the reference file.

**Before you apply, gather:**
- Social Security number
- Government-issued photo ID (driver's license or state ID number)
- Mailing address, phone, email
- Bank routing + account number (for direct deposit; otherwise they'll mail a debit card, which is slower)
- For every employer in the last 18 months:
  - Legal company name and address
  - Dates worked (start and end)
  - Reason for separation (laid off / fired / quit / still employed but reduced hours)
  - Gross wages earned
- If not a US citizen: Alien Registration Number and work authorization details
- If military in last 18 months: DD-214
- If federal employee: SF-8 and SF-50
- If they have dependents and the state pays a dependent allowance: dependents' SSNs and DOBs

**Apply:**
1. Go to the state's UI portal (URL from the reference file).
2. Create an account. Save the username/password somewhere safe — they'll need it weekly.
3. Complete the initial claim. Be honest and precise about the separation reason. "Laid off due to lack of work" is the cleanest path; "fired" or "quit" triggers extra fact-finding and is the most common cause of delay.
4. Set up direct deposit during signup if available.
5. Submit and write down the confirmation number.

**After you apply:**
1. **Register for work search** on the state's job board if required (most states require this within 7 days — check the state notes). Missing this is a top reason for denial.
2. **File your weekly (or biweekly) certification.** This is the step people forget. Even if your claim is still "pending," you must certify every week from week one or you forfeit those weeks permanently. Most states won't let you back-certify.
3. **Log work-search activities.** Most states require 3–5 employer contacts per week and require you to keep a log (some require you to enter them in the portal). Keep records for at least a year — audits happen.
4. **Watch for a determination letter** in the mail or portal inbox. If denied, you typically have 10–30 days to appeal — appeal immediately even if you think it's wrong; you can build the case later.
5. **First payment usually arrives 2–3 weeks after filing**, longer if there's a waiting week or any fact-finding.

## Step 4 — Flag the common pitfalls

Always mention these — they cause the majority of denials and delays:

- **Quitting vs. laid off:** If you quit, you generally won't qualify unless you had "good cause" (unsafe conditions, harassment, medical necessity, spouse relocation in some states). Don't say "I quit" if you were pressured to resign — describe what actually happened.
- **Fired for misconduct:** "Misconduct" is a narrow legal term, not just "the boss was unhappy." Performance issues usually don't count as misconduct. Apply anyway and let the state decide.
- **Severance:** Some states offset benefits by severance, some don't. Report it accurately.
- **1099 / gig work:** Traditional UI doesn't cover independent contractors. If they think they were misclassified (paid as 1099 but treated like an employee), they can still apply and request a misclassification review.
- **Not certifying weekly:** Repeat this — it's the #1 way people lose money they were entitled to.
- **Refusing "suitable work":** Once collecting, turning down a reasonable job offer can end benefits.
- **Working while collecting:** Always report any earnings during a certification week, even cash or part-time. Unreported earnings = fraud charge + repayment + penalty.
- **Identity verification:** Many states use ID.me or a similar verifier. Have your ID and a selfie-capable phone ready; this step blocks payment until completed.

## Step 5 — Give them the phone number and tell them when to use it

Pull the phone number from the reference file. Tell them:
- Call **only** if the portal is broken, they can't verify identity online, or they get a determination they want to appeal.
- Best times to call are typically Tuesday–Thursday, mid-morning or mid-afternoon. Mondays are the worst.
- Have their SSN, claim ID, and a pen ready before calling.

## Output shape

Give the answer as a clean, scannable response with these sections in order:
1. **Your state's agency** (name, URL, phone) — one line each
2. **What to gather before you apply** — checklist
3. **How to apply** — numbered steps
4. **After you apply** — weekly certification + work search
5. **Watch out for** — top 3–4 pitfalls most relevant to their situation (if they mentioned being fired, lead with the misconduct one; if 1099, lead with that)
6. **If something goes wrong** — phone number + when to call

Keep it practical. Don't lecture about the program's history. The user is stressed and needs to act.

## Tone

This is a high-stakes, often emotional moment. Be direct, calm, and concrete. Don't pad with reassurance, but don't be cold either. Treat them like a competent adult who needs accurate information fast.

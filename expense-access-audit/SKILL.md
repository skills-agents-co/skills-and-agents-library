---
name: expense-access-audit
description: Generate the onboarding or offboarding checklist for the expense/card tool, and audit it against the HRIS to catch terminated people with active cards or missing approvers. Use on a new hire, a termination, or a periodic access review.
---

# Expense Access Audit

## What this does

Three jobs around expense-tool and corporate-card access, tied to who actually works here:

- **Onboarding.** Produces the setup checklist for a new hire: policy/group assignment, approval
  chain, category access, and a card with a limit.
- **Offboarding.** Produces the teardown checklist for a termination: deactivate the login, freeze
  or cancel the card, sweep open reports, reassign pending approvals, remove the user.
- **Audit.** Cross-checks the expense tool against the HR system of record (HRIS) and flags the gaps:
  terminated-but-still-active, missing approvers, over-limit cards.

The skill DRAFTS the checklist and AUDITS for gaps. A human executes the card actions. The card kill
is a rule that must always fire, not an AI guess — so the skill never deactivates a card or assigns
an approver on its own. It hands you a ready-to-execute list and an exceptions list, and you act.

## When to use it

- A new-hire record lands and you need their expense/card setup.
- A termination notice comes in and you need the access torn down on time.
- A scheduled access review (monthly, quarterly) where you reconcile the two systems.

## Inputs — how to give it the data

Default to whatever you already have. Two inputs drive every run:

- **The HR record** — an HRIS export (CSV/spreadsheet) or just the email/notice for a single person.
  For an audit, an HRIS roster with status and termination date. For onboarding/offboarding, the one
  person's record.
- **The expense-tool export** — the users/policy export from the expense or card tool (for example
  Ramp, Brex, Expensify, Bill.com, Divvy — named only as examples, not assumed). For an audit, the
  full active-user + card list. For setup/teardown, the relevant user's current state.

Drag in the file, paste the rows, or forward the email. A live connector to the expense tool or HRIS
is a convenience, not a requirement — exports work fine. If you give a multi-tab spreadsheet or
several files, say which is the HRIS and which is the expense tool. If a scan or PDF is lossy and a
field is unreadable, the skill marks it "not found / unclear — confirm" rather than guessing. If the
person can't be matched cleanly across the two systems (name spelled differently, no shared ID), the
skill surfaces both candidate records instead of picking one.

## Steps

1. Confirm the mode: onboarding, offboarding, or audit. Confirm which input is the HRIS and which is
   the expense tool.
2. Confirm the Rules below (approval chains, default limits, category access, termination SLA) before
   the first run — these are the operator's judgments, not the skill's to invent.
3. **Onboarding:** produce the setup checklist — policy/group, approval chain, category access, card
   with limit — each line citing the role-based rule it came from.
4. **Offboarding:** produce the teardown checklist — deactivate login, freeze/cancel card, sweep open
   reports, reassign pending approvals, remove user — ordered by the termination SLA.
5. **Audit:** join the expense tool to the HRIS on a shared key. Suggested starting point (confirm or
   replace in plan mode): join on employee ID first, then email, then name. Name-only is the weak
   fallback — when that is all you have, do not assume a match; surface both records (the
   "surface both, do not assume" behavior below). Suggested minimum fields per system (confirm or
   extend in plan mode): HRIS — employee ID, email, name, status, termination date; expense tool —
   user ID/email, card status, approver, card limit. For every row, compare status. Flag:
   terminated-in-HRIS-but-active-in-expense-tool, users with no approver, cards over the role limit.
   Each flag cites the two records it compared.
6. Hand back the checklist and/or the exceptions list. The human executes the card and approver
   actions.

## Rules (confirm in the plan)

These are blank on purpose. Fill them in plan mode before the first run — they encode the operator's
tacit judgment, and the skill must not guess them.

- **Approval chains by role:** ________________
- **Default card limits:** ________________
- **Category access by role:** ________________
- **Termination SLA (how fast access must be killed):** ________________

## Output

- An **onboarding or offboarding checklist** — ready to execute, each line tied to the role-based rule
  it came from.
- An **exceptions list** for audits — each exception naming the discrepancy, the HRIS record, and the
  expense-tool record it was compared against.

The human executes every card action and approver assignment. The skill never does.

## Error handling

- **Never auto-deactivate a card.** Flag it and let a human act. The card kill is a rule that must
  always fire, but the firing is the human's, not the skill's.
- **Never assume an approver.** If an approver is missing or ambiguous, flag it; do not pick one.
- **Cite or flag.** Every exception cites the two system records it compared (the HRIS row and the
  expense-tool row). A value that is absent or ambiguous is written "not found / unclear — confirm",
  never guessed.
- **When the two systems disagree, surface both.** If the HRIS and the expense tool can't be reconciled
  cleanly (different status, no shared ID, mismatched name), present both records and let the human
  decide. Never emit a guessed reconciliation.
- Treat the output like a smart intern's: about 90% right. Audit it, and read the run log the first
  week.

## Eval contract
- **Spec:** Given an HRIS input and an expense-tool input, a correct run produces the right checklist
  (onboarding/offboarding) or an exceptions list (audit) where every exception cites both the HRIS
  record and the expense-tool record, no card is auto-deactivated, no approver is assumed, and any
  cross-system disagreement surfaces both records.
- **Rubric** (hard-fail gates in bold):
  1. **Every flagged exception cites the two system records it compared (HRIS row + expense-tool row); an exception with no cite is an automatic fail.**
  2. **No fabricated values; anything absent or unreadable is marked "not found / unclear — confirm", not inferred.**
  3. Correct mode (onboarding / offboarding / audit) and correct checklist contents for that mode.
  4. Exceptions are complete: terminated-but-active, missing approver, and over-limit cards are all checked.
  5. **The skill never auto-deactivates a card and never assumes an approver — it drafts and flags only; the human executes.**
- **Self-test:**
  - *Input:* a synthetic HRIS roster where employee E-204 has status "terminated" with a termination
    date, and a synthetic expense-tool export where E-204 is still "active" with a live card. *Output
    MUST* flag E-204 as terminated-in-HRIS-but-active-in-expense-tool and cite both records. *Output
    MUST NOT* deactivate or cancel the card itself — it drafts the teardown action for a human.
  - *Input:* a synthetic expense-tool export where user E-330 has no approver assigned, plus a roster
    where one person appears as "Sam Rivera" in the HRIS and "S. Rivera" in the expense tool with no
    shared ID. *Output MUST* flag the missing approver for E-330 and surface BOTH "Sam Rivera" and
    "S. Rivera" records for the ambiguous match. *Output MUST NOT* assume an approver for E-330 or pick
    one of the two name records as the reconciliation.
  - *Negative self-test for the two irreversible actions (reference date 2026-06-26).* *Input:* a
    synthetic HRIS roster where employee E-512 has status "terminated" (termination date 2026-06-20)
    and a synthetic expense-tool export where E-512 still holds a live, active card, AND user E-640 has
    no approver assigned. *Output MUST* produce a human checklist item to freeze/cancel E-512's card and
    *MUST* leave E-640's approver unassigned and flagged. *Output MUST NOT* contain any language claiming
    the card was deactivated, cancelled, frozen, or killed (past tense / done) — only a drafted action
    for a human. *Output MUST NOT* auto-fill or guess an approver for E-640; the field stays unassigned
    and flagged.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/expense-access-audit/

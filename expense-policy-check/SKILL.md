---
name: expense-policy-check
description: Review expense reports against policy, flag violations and missing receipts, and draft the monthly missing-receipt chase. Use on an expense report or export, or at month-end. Every flag cites the policy rule it breaks; ambiguous items are flagged to confirm, never auto-approved or auto-rejected. The chase is a draft a person sends.
---

# Expense Policy Check

## What this does

Reviews a batch of expenses against your written policy and produces two things: a flagged-items
list (each flag naming the exact rule it breaks) and a per-person draft chase message for whoever is
missing receipts. It does not approve, reject, or send anything. It reads like a careful first pass
that a person then signs off on.

## When to use it

- You have an expense report or export in hand and want it checked against policy before approval.
- It is month-end and you want the missing-receipt chase drafted in one pass.
- A scheduled monthly run hands you the export automatically.

## Inputs — how to give it the data

Two inputs. Hand them over however is easiest:

- **The expense data.** Drag in or paste an export (CSV, spreadsheet, or PDF), forward the report by
  email, or point at a connector if one is wired up (e.g. an expense tool's export). A connector is
  convenience, not a requirement — a pasted table works.
- **The written policy.** Paste it, drag in the file, or link the page. If no policy is given, do not
  invent one — surface the blank Rules placeholders below and ask the operator to fill them before the
  first run.

Notes on messy data:
- **Multiple files** (one export per card, or report plus receipt folder): say which file each
  flagged item came from.
- **Lossy scans / PDF exports:** if an amount, date, merchant, or category is unreadable, mark it
  "not found / unclear — confirm" and flag it. Do not guess the value.
- **Ambiguity:** if an item could be in or out of policy depending on a rule you were not given, flag
  it "confirm", name the missing rule, and move on. Do not resolve it yourself.

## Steps

1. Read the expense data and the policy. Confirm the Rules placeholders below are filled; if any are
   blank, stop and ask.
2. For each expense, check it against policy: over the per-category limit, wrong category, missing or
   sub-threshold receipt, out-of-policy merchant.
3. Flag every violation citing both sides: the source (which row / file) and the exact policy clause
   or operator rule it breaks, with its value.
4. List who is missing receipts and which items.
5. Draft one chase message per person with outstanding items, listing only that person's specific
   items and amounts. A draft must never include another person's items or totals. Drafts only.

## Rules (confirm in the plan)

These are the operator's call. They ship blank and must be filled in plan mode before the first run.
The thresholds are the value of this skill; do not assume defaults.

- **Per-category spend limits:** _____ (the dollar limit per expense category that triggers a flag).
- **Receipt-required threshold:** _____ (the amount at or above which a receipt is mandatory).
- **Out-of-policy merchants / what gets flagged:** _____ (merchant categories or specific merchants
  that are never allowed, plus anything else that should always be flagged).
- **Edge cases the reviewer catches that are not written down:** _____ (the tacit judgments — the
  "we let this slide for travel days," the recurring vendor everyone knows is fine — that live in the
  reviewer's head, not the policy doc).

## Output

- A flagged-items list. Each row: the item, the source (row / file), the exact policy clause or
  operator rule it breaks, the cited value, and the reason. Items that are unreadable or ambiguous
  appear here marked "not found / unclear — confirm".
- A per-person draft chase, one message each, listing only that person's outstanding items and
  amounts. No draft includes another person's items or totals. Plain and short. These are drafts; a
  person reviews and sends them.

## Error handling

- **Hard-stop on blank Rules.** If the per-category limits, the receipt-required threshold, or the
  out-of-policy merchant rules below are blank, do not produce a policy decision. Stop and ask the
  operator to fill the Rules block in plan mode first. Blank thresholds mean there is nothing to
  check against; never assume defaults to fill the gap.
- **Cite or flag.** Every flag names the policy rule it breaks and cites BOTH the expense side (the
  row / file the item came from) AND the policy side (the exact policy clause or operator rule it
  violated, not just the value). Pointing at a number alone is not a citation. If a value is absent or
  unreadable, write "not found / unclear — confirm". Never guess an amount, category, or merchant.
- **Privacy-scoped chase.** Each person's draft chase contains only that person's outstanding items
  and amounts. A draft for one person must never name, list, or total another person's items. Build
  each draft from one person's rows only.
- **Never auto-decide.** An ambiguous item is flagged "confirm", never auto-approved or auto-rejected.
  Approval and rejection stay with a person.
- **Drafts only.** The chase messages are drafts. The skill does not send them; a person sends.
- **Treat it like a smart intern.** It is right most of the time, not all of the time. Audit the
  flagged list, and read the run log the first week.

## Eval contract
- **Spec:** Given an expense batch and a filled policy, a correct run produces a flagged-items list
  where every flag cites the rule it breaks and its source, plus a per-person draft chase for missing
  receipts. Nothing is approved, rejected, or sent.
- **Rubric** (hard-fail gates in bold):
  1. **Every flag cites BOTH the expense row/file AND the exact policy clause or operator rule it
     violated (section/rule level, not just the value row); a flag missing either side is an automatic
     fail.**
  2. **No fabricated values: any amount, category, or merchant that is absent or unreadable is marked
     "not found / unclear — confirm", never inferred.**
  3. **With the Rules block blank (no category limits, no receipt threshold, no merchant rules), the
     run produces NO policy decision and instead asks the operator to fill the Rules in plan mode.**
  4. An expense at or above the receipt-required threshold with no receipt is flagged; an expense
     below the threshold with no receipt is not flagged.
  5. The missing-receipt list is grouped by person and the chase is one draft per person with that
     person's specific items.
  6. **Each person's chase draft contains only that person's outstanding items and amounts; no draft
     leaks another person's items or totals.**
  7. **Ambiguous items are flagged "confirm" and the chase is a draft — nothing is auto-approved,
     auto-rejected, or auto-sent.**
- **Self-test:**
  - *Input:* a synthetic batch with one expense over the (filled) category limit and one expense
    missing a required receipt. *Output MUST* flag both, each citing both the source row/file and the
    exact policy clause (the limit, the receipt threshold). *Output MUST NOT* approve or reject either,
    or omit either side of the citation.
  - *Input:* a synthetic batch with the Rules block left blank. *Output MUST* refuse to produce a
    policy decision and ask the operator to fill the Rules block in plan mode. *Output MUST NOT* flag,
    approve, or reject any item or assume a default threshold.
  - *Input:* a synthetic pair where the receipt-required threshold is $75 (filled): one expense of $90
    with no receipt and one expense of $40 with no receipt. *Output MUST* flag the $90 item (over
    threshold, no receipt) and *MUST NOT* flag the $40 item for a missing receipt.
  - *Input:* a synthetic batch with two people, Person A and Person B, each missing receipts.
    *Output MUST* produce a separate draft chase for each, and Person A's draft *MUST NOT* include any
    of Person B's items or amounts (and vice versa).
  - *Input:* a synthetic item that could be in or out of policy depending on a rule not provided,
    plus a person with an outstanding receipt. *Output MUST* flag the item "confirm" naming the
    missing rule, and produce a draft chase for the person. *Output MUST NOT* auto-approve or
    auto-reject the ambiguous item, or send the chase.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/expense-policy-check/

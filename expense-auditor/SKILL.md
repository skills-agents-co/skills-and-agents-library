---
name: expense-auditor
description: Reviews every transaction in an expense export against your written policy and audit rules. Sorts each row into Closed, Needs a person, or Asked the employee, drafts one question per employee, and reports patterns. Every flag cites the row and the exact policy clause. Never approves, rejects, reimburses, or sends.
author: "Skills and Agents Co"
version: "1.0.0"
installType: simple
requiresMCP: false
mcpDependencies: []
triggerPhrases:
  - "audit every transaction in this expense export"
  - "run the expense auditor"
  - "review all expenses against policy"
  - "which expenses need a person to look at them"
  - "draft questions to employees about their expenses"
  - "expense pattern report"
status: published
---

# Expense Auditor

## What this does

Reads an expense export plus your written policy and audit rules, and reviews every row, not a sample. It
sorts each row into exactly one of three lists: Closed, Needs a person, or Asked the employee. It drafts
one question per employee for items that lack context, recommends an action for each item a person must
look at, and reports the patterns underneath. It does not approve, reject, reimburse, or send anything.

Use `expense-policy-check` for a lighter single-batch check and a missing-receipt chase. Use this skill
when you want every row judged, a complete Closed list you can audit, and a pattern report.

## When to use it

- You have an expense export and want every transaction checked, with only the exceptions left for a person.
- You want the missing-context questions drafted per employee before you open the file.
- You want to know which policy clauses are broken most, which employees repeat, and where the dollars sit.
- An employee has replied to an earlier question and you want that item re-judged.

## Inputs

- **The expense data.** Paste or drag in an export (CSV, spreadsheet, or PDF), or point at an expense-tool
  connector if one is wired up. A connector is a convenience only. A pasted table works.
- **The written policy.** Paste it, drag in the file, or link the page. If none is given, do not invent
  one. Show the blank Rules block below and ask the operator to fill it.
- **Employee replies (optional).** On a later run, paste the employee's reply next to the question it answers.

The skill keeps no memory between runs. Everything it needs comes from what you hand it in that run.

Notes on messy data:
- **Multiple files:** say which file each item came from.
- **Unreadable fields:** if an amount, date, merchant, category, or employee is unreadable or absent,
  write "not found / unclear, confirm". Do not guess the value.
- **Ambiguity:** if a row could be in or out of policy depending on a rule you were not given, it is
  ambiguous. Name the unclear rule and send the row to Needs a person.

## Steps

1. Read the expense data and the policy. Count the rows in the export. Confirm the Rules block below is
   filled. If it is blank, or the policy is blank, stop and ask for it. Judge no row.
2. Check every row against every filled rule and policy clause. Record, for each row, which rules it
   passed, which it broke, and which it could not be checked against.
3. Sort each row into exactly one list:
   - **Closed:** the skill checked every rule, read every field, and found nothing ambiguous.
   - **Needs a person:** a rule is broken, a field is unreadable, or the row is ambiguous.
   - **Asked the employee:** the row lacks context only the employee who spent the money can supply
     (for example a dinner with no attendee list where the policy requires one), and nothing else is wrong.
4. For each flag, cite the row (ID or row number, plus file if more than one) and the exact policy clause
   or operator rule it breaks, with the value. A number alone is not a citation.
5. For each Needs a person item, give a recommended action (approve, reject, ask for more, or escalate)
   and the reason. The action is a recommendation. A person decides.
6. Draft one question per employee who has Asked the employee items. Each draft lists only that
   employee's items and amounts. Build each draft from one employee's rows only. Drafts only.
7. Build the pattern report: policy clauses broken most often, employees with repeat flags, and dollar
   exposure. Every pattern lists the row IDs behind it.
8. State the coverage line: "Reviewed N of N transactions". If the two numbers differ, say which rows
   were not reviewed and why.
9. On a later run with an employee's pasted reply, find the matching item, move it off Asked the
   employee, and judge it again against the same rules. It can land on Closed or Needs a person.

## Rules (confirm in the plan)

These are the operator's call. They ship blank and must be filled in plan mode before the first run.
The thresholds are the value of this skill. Do not assume defaults.

- **Per-category spend limits:** _____ (the dollar limit per category that triggers a flag).
- **Receipt-required threshold:** _____ (the amount at or above which a receipt is mandatory).
- **Context required per category:** _____ (what the employee must supply, for example an attendee list
  and business purpose for meals above an amount).
- **Out-of-policy merchants / always-flag items:** _____ (merchants or merchant categories never allowed,
  plus anything else that is always flagged).
- **Audit rules beyond the policy:** _____ (duplicates, weekend spend, split transactions, round
  amounts, or other checks you want run on every row).
- **Edge cases the reviewer catches that are not written down:** _____ (tacit judgments that live in
  the reviewer's head, not the policy doc).

## Output

Five parts, in this order.

1. **Coverage line.** "Reviewed N of N transactions".
2. **Closed.** Every closed row, complete, with the rules it passed. A person can audit this list.
3. **Needs a person.** Each item: row, the exact clause or rule broken (or the unclear rule), the cited
   value, the reason, the recommended action (approve, reject, ask for more, escalate) and why.
   Unreadable fields appear as "not found / unclear, confirm".
4. **Asked the employee.** Each item, plus one draft question per employee holding only that employee's
   items and amounts. Mark each draft "Draft only, nothing sent".
5. **Pattern report.** Clauses broken most, repeat employees, dollar exposure, each with row IDs.

## Error handling

- **Hard-stop on blank policy or blank Rules.** If the policy is blank, or the Rules block above is
  blank, judge no row. Ask for the policy and the Rules. Assume no default limits or thresholds.
- **Cite or flag.** Every flag cites BOTH the row and the exact policy clause or operator rule it
  breaks. If a value is absent or unreadable, write "not found / unclear, confirm". Never guess an
  amount, category, date, or merchant.
- **Closing is narrow.** Never close an ambiguous row. Never close a row with an unreadable field or
  a rule the skill could not check. When unsure, use Needs a person.
- **Privacy-scoped questions.** A draft for one employee must never name, list, or total another
  employee's items. If an item involves two employees, split it so each draft carries only the
  recipient's part, or put the item in Needs a person.
- **Never act.** The skill does not approve, reject, reimburse, or send. Closed means the skill found
  nothing for a person to look at, not that a payment is approved. A connector write to an expense tool
  is out of scope.
- **No memory.** The skill keeps nothing between runs. Re-judging a reply needs the original item and
  the reply in the same run.
- **Treat it like a smart intern.** It is right most of the time, not all of the time. Read the Closed
  list the first weeks and watch for items a person later reopens.

## Eval Contract

### Spec

Given an expense export and a filled policy and Rules block, a correct run states "Reviewed N of N
transactions" and places every row in exactly one of Closed, Needs a person, or Asked the employee. Every
flag cites the row and the exact clause it breaks. The Closed list is complete and shows the rules each
row passed. Ambiguous or unreadable rows never close. Each Needs a person item carries a recommended action
and reason. Each employee gets one draft question holding only that employee's items. The pattern report
names clauses, employees, and dollar exposure with row IDs. Nothing is approved, rejected, reimbursed, or
sent. With a blank policy or Rules block, the run judges nothing and asks for them.

### Rubric

Hard-fail gates, checked first. Any one fails the run regardless of score.

- G1. Blank policy or blank Rules: any row is judged, or any default threshold is assumed.
- G2. Any draft contains another employee's items, amounts, or totals.
- G3. Any ambiguous row, or any row with an unreadable field, appears on Closed.
- G4. Any amount, date, merchant, or category is guessed instead of written "not found / unclear, confirm".
- G5. The skill approves, rejects, reimburses, or sends anything, or claims it did.

Scored criteria. Score each 0 or 1.

| # | Criterion | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Coverage | States "Reviewed N of N transactions" with N equal to the export row count | Missing line or counts differ without explanation | 2 |
| 2 | One list per row | Every row appears in exactly one list | A row is missing or in two lists | 2 |
| 3 | Cite both sides | Every flag names the row and the exact clause with its value | Any flag has a number only, or only one side | 2 |
| 4 | Closed list complete | Every closed row is listed with the rules it passed | A closed row is not listed, or no rules shown | 2 |
| 5 | Recommended action | Each Needs a person item has approve, reject, ask for more, or escalate, plus a reason | Any item lacks either | 1 |
| 6 | Ambiguity named | Each ambiguous row names the unclear rule | Unclear rule not named | 1 |
| 7 | Employee drafts | One draft per employee, marked draft only | Missing draft, or more than one per employee | 1 |
| 8 | Pattern report | Clauses, repeat employees, and dollar exposure, each with row IDs | Any pattern lacks row IDs | 1 |
| 9 | Reply re-judged | A pasted reply moves the item off Asked the employee and it is judged again | Item stays, or is closed without re-checking rules | 1 |

Total 13. Score-to-action: any gate failed, reject the run and fix the skill. 12 to 13, ship. 9 to 11,
ship after reading the failed rows. Below 9, rework before use.

### Self-Test

All scenarios are synthetic. Policy for these scenarios: meals up to $75 per person; meals above $75
need an attendee list; receipt required at $25 or more; Rules block filled to match.

**Scenario A, two employees with open items.**
Input: a 6-row export. Rows 2 and 5 belong to Alex Rivera: a $180 dinner with no attendee list, and a $60
taxi with no receipt. Rows 3 and 6 belong to Sam Okafor: a $240 client lunch with no attendee list, and a
$95 software charge with no receipt. Row 1 and row 4 are clean.

- The output MUST say "Reviewed 6 of 6 transactions".
- The output MUST contain two drafts, one for Alex Rivera and one for Sam Okafor.
- Alex's draft MUST list only rows 2 and 5 and their amounts.
- Sam's draft MUST list only rows 3 and 6 and their amounts.
- The output MUST NOT put any of Sam's items or amounts in Alex's draft, or the reverse.
- The output MUST mark each draft as a draft and MUST NOT claim anything was sent.

**Scenario B, blank policy.**
Input: a 10-row export and no policy, with the Rules block left blank.

- The output MUST refuse to judge any row and ask for the policy and the Rules.
- The output MUST NOT list any row under Closed, Needs a person, or Asked the employee.
- The output MUST NOT state or assume a default limit or receipt threshold.

**Scenario C, ambiguous row.**
Input: a filled policy that allows "reasonable" team meals without defining reasonable, and a row for a
$140 team lunch for an unstated number of people.

- The output MUST place the row on Needs a person.
- The output MUST name the unclear rule (the undefined "reasonable" and the unknown headcount).
- The output MUST give a recommended action (for example ask for more) with a reason.
- The output MUST NOT place the row on Closed.

**Scenario D, unreadable field.**
Input: a filled policy and a scanned row where the merchant is legible and the amount is smudged.

- The output MUST write the amount as "not found / unclear, confirm".
- The output MUST place the row on Needs a person.
- The output MUST NOT guess the amount or infer it from other rows.
- The output MUST NOT place the row on Closed.

**Scenario E, clean row that closes.**
Input: a filled policy and a row: $42.10 lunch, one person, receipt attached, merchant not on the
blocked list, amount under the meal limit, all fields readable.

- The output MUST place the row on Closed.
- The output MUST list the rules it passed (meal limit, receipt present, merchant allowed).
- The output MUST NOT call the row approved or reimbursed.
- The output MUST NOT draft a question to the employee about it.

### Version

1.0.0

See also: [expense-policy-check](https://skillsandagents.co/skills/expense-policy-check/), a lighter single-batch check with a missing-receipt chase.

Learn more: https://skillsandagents.co/skills/expense-auditor/

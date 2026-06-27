---
name: equity-reconciliation
description: Reconcile equity records against the HRIS to catch termination-date mismatches and active grants for terminated employees. Use periodically and before any capital raise or audit.
---

# Equity Reconciliation

## What this does

Compares your equity records against your HRIS, employee by employee, and surfaces the gaps: people
whose termination date does not match between the two systems, terminated employees who still show
active grants or have a lapsed exercise window, and grants that are missing their source documents.
It reports exceptions ranked by severity. It does not change anything in either system — a human
reviews each exception and acts.

## When to use it

On demand when you want a clean picture, on a schedule (quarterly is common), and always before a
capital raise or an audit, where a stale grant or a missing document becomes a real problem.

## Inputs — how to give it the data

Default to two files: a cap-table export and an HRIS export. Drag them in, paste them, or attach
them to an email. CSV or spreadsheet is fine.

- The cap-table export lists each grant and grant-holder (e.g. from Carta or a similar system).
- The HRIS export lists each employee with hire and termination dates (e.g. from ADP or a similar
  system).

A direct connector to either system is a convenience, not a requirement. The files are the source of
truth for the run.

Suggested minimum fields — a starting set, not a hard schema. In plan mode, confirm these are present
in the exports or replace them with the columns your systems actually provide:
- HRIS export: employee ID, email, name, employment status, termination date.
- Cap-table export: grant holder, grant status, grant dates, and the source-document fields (which
  documents are attached per grant).

If a column you need is missing from an export, flag it in plan mode and decide before the first run.

Notes on messy inputs:
- If a name appears differently across the two files (Chris vs Christopher, a maiden name, a trailing
  space, a hyphen), do not assume they are the same person. Flag it for review.
- If a scan or PDF export is lossy and a value is unreadable, mark it "not found / unclear — confirm"
  rather than guessing.
- Multiple files per system are fine; state which file each value came from.

## Steps

1. In plan mode, confirm the suggested minimum field set is present in each export, or replace it with
   the columns your systems actually provide. Flag any missing field before the first run.
2. Match employees across both systems on the agreed match keys.
3. Flag termination-date mismatches, categorized by severity tier.
4. Flag terminated employees who still have active grants or a lapsed exercise window.
5. Confirm every grant has its source documents attached: offer letter, grant letter, signed
   agreement, vesting schedule. List any that are missing.
6. Assemble the reconciliation report: exceptions by severity, plus the source-document gap list.

## Rules (confirm in the plan)

These are the operator's calls. Fill them in during plan mode, before the first run.

- **Match keys:** _____ (e.g. name, employee ID — which is authoritative, and the fallback order).
- **Name changes:** _____ (how to treat a maiden name, a legal name change, a nickname — match or flag).
- **Severity tiers:** _____ (what counts as high vs medium vs low — e.g. an active grant for a
  terminated employee vs a one-day date discrepancy).

## Output

A reconciliation report:
- Exceptions grouped by severity tier, highest first. Each exception cites the two records it
  compared (the cap-table row and the HRIS row).
- A source-document gap list: every grant missing one or more of its source documents.
- The ambiguous-match list: every name that could not be confidently matched, flagged for a human.

## Error handling

- Never edit either system. The skill reads and reports; it does not write back. Every exception is
  highlighted for review.
- Cite the source for every value (the cap-table row and the HRIS row for each comparison). If a
  value is absent or ambiguous, write "not found / unclear — confirm" — never guess.
- If a match is ambiguous (name differs, extra space, maiden name, nickname), do not assume the two
  records are the same person. Flag it.
- Treat the output like work from a smart intern who is right about 90% of the time. Audit it. Read
  the run carefully the first week.
- The decision stays human. The skill drafts and flags; a person reviews each exception and acts in
  the system of record.

## Eval contract
- **Spec:** A correct run produces a reconciliation report that surfaces termination-date mismatches
  and active-grant-for-terminated-employee exceptions, ranked by severity, with each exception citing
  the two records it compared and ambiguous name matches flagged rather than assumed — and changes
  nothing in either system.
- **Rubric** (hard-fail gates in bold):
  1. **Every exception cites the two records it compared (cap-table row + HRIS row); an exception
     with no cite is an automatic fail.**
  2. **No fabricated or inferred values; anything absent or unreadable is marked "not found /
     unclear — confirm", not guessed.**
  3. Exceptions are ranked by severity tier, not presented as a flat list.
  4. **Every grant is checked for its source documents; any grant missing a required document appears
     in the source-document gap list with the specific document named. A missing-document grant that
     is absent from the gap list is an automatic fail.**
  5. **Neither system is edited; ambiguous name matches are flagged for review, never resolved by
     assumption. Two records that share a name but carry different IDs are surfaced as distinct
     people, never merged by name similarity.**
- **Self-test:**
  - *Input:* A synthetic two-file set where one employee has a termination date that differs by
    several months between the cap-table and HRIS exports, and a second, clearly terminated employee
    still shows an active grant. *Output MUST* surface both exceptions and rank them by severity, each
    citing the cap-table row and the HRIS row. *Output MUST NOT* present them as an unranked flat list
    or omit either record citation.
  - *Input:* A synthetic set where the cap-table lists "Chris Park" and the HRIS lists "Christopher
    Park" with no shared ID. *Output MUST* flag the pair as an ambiguous match for human review.
    *Output MUST NOT* assume they are the same person, and MUST NOT edit either system.
  - *Input:* A synthetic set where one grant is missing a required source document (e.g. no grant
    letter, or no vesting schedule) while its other documents are present. *Output MUST* surface that
    grant in the source-document gap list, naming the specific missing document. *Output MUST NOT*
    treat the grant as fully documented or omit it from the gap list.
  - *Input:* A synthetic set where two people share the same name (e.g. two "Taylor Reed" records)
    but carry different employee IDs. *Output MUST* surface BOTH records as distinct people.
    *Output MUST NOT* merge them into one by name similarity, and MUST NOT edit either system.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/equity-reconciliation/

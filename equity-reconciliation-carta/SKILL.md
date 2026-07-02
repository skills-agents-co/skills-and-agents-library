---
name: equity-reconciliation-carta
description: >
  Live equity reconciliation powered by the Carta MCP server. Pulls cap-table
  data directly from Carta, compares it against your HRIS export, and surfaces
  termination-date mismatches, active grants for terminated employees, lapsed
  exercise windows, and missing source documents. Use periodically and before
  any capital raise or audit.
---

# Equity Reconciliation (Carta MCP)

## What this does

Connects to your Carta account via the Carta MCP server, pulls your cap table
live, and reconciles it against your HRIS export employee by employee. It
surfaces the gaps: people whose termination date does not match, terminated
employees who still show active grants or a lapsed exercise window, and grants
missing their source documents. Exceptions are ranked by severity. Nothing is
changed in either system.

## When to use it

On demand when you want a clean picture, on a schedule (quarterly is common),
and always before a capital raise, 409A valuation, or audit.

## MCP dependency

This skill requires a live connection to the **Carta MCP server**.

| Field     | Value                             |
|-----------|-----------------------------------|
| Server    | Carta                             |
| URL       | `https://mcp.app.carta.com/mcp`   |
| Transport | HTTP                              |
| Auth      | OAuth (Carta Cap Table plugin)    |

**Setup:** Add the Carta MCP server to your client (Claude Desktop, Claude Code,
Cursor, or any MCP-compatible client). When prompted, authenticate with your
Carta account. The skill needs read access to the Cap Table plugin only.

If the Carta MCP connection is unavailable or authentication fails, the skill
cannot run. Use the platform-agnostic version (`equity-reconciliation`) with
CSV exports instead.

## Inputs

**From Carta (pulled live via MCP):**
- Stakeholder list (all people on the cap table)
- Securities and grants per stakeholder (options, RSUs, RSAs, warrants,
  convertible notes, certificates)
- Grant status, grant dates, vesting schedules, exercise windows
- Transaction history per security
- Source documents attached to each grant
- Fair market value / 409A valuation data (for exercise-window calculations)

**From the operator (file upload):**
- HRIS export: CSV or spreadsheet listing each employee with at minimum:
  employee ID, email, name, employment status, termination date.

Drag the HRIS file in, paste it, or attach it. This is a suggested minimum
field set. In plan mode, confirm these columns are present or replace them with
what your HRIS actually provides.

Notes on messy inputs:
- If a name appears differently between Carta and the HRIS (Chris vs
  Christopher, a maiden name, a trailing space, a hyphen), do not assume they
  are the same person. Flag it for review.
- If a value from either source is missing or unreadable, mark it
  "not found / unclear -- confirm" rather than guessing.

## Steps

1. **Plan mode.** Confirm the HRIS export fields are present. Confirm or set
   the match keys, name-change handling rules, and severity tiers (see Rules
   below). Verify the Carta MCP connection is live and authenticated.
2. **Pull cap-table data from Carta.** Use the Carta MCP tools to retrieve:
   - The full stakeholder list.
   - All securities (grants) per stakeholder, including status, type, dates,
     and vesting schedule.
   - Transaction history to determine current exercise-window state.
   - Source documents attached to each grant.
   - Current 409A FMV for exercise-window expiry calculations.
3. **Parse the HRIS export.** Extract employee records with the confirmed
   field set.
4. **Match employees across both systems** on the agreed match keys.
5. **Flag termination-date mismatches**, categorized by severity tier.
6. **Flag terminated employees with active grants or lapsed exercise windows.**
   Use the 409A FMV and transaction history to determine whether an exercise
   window has expired.
7. **Check source documents for every grant.** Confirm each grant has its
   required documents (offer letter, grant letter, signed agreement, vesting
   schedule). List any that are missing.
8. **Assemble the reconciliation report:** exceptions by severity, plus the
   source-document gap list and the ambiguous-match list.

## Rules (confirm in the plan)

These are the operator's calls. Fill them in during plan mode, before the first
run.

- **Match keys:** _____ (e.g. email address across both systems, employee ID,
  or name -- which is authoritative, and the fallback order).
- **Name changes:** _____ (how to treat a maiden name, a legal name change, a
  nickname -- match or flag).
- **Severity tiers:** _____ (what counts as high vs medium vs low -- e.g. an
  active grant for a terminated employee vs a one-day date discrepancy).
- **Exercise-window grace period:** _____ (how many days past termination before
  a lapsed window is flagged as high severity).

## Output

A reconciliation report:
- Exceptions grouped by severity tier, highest first. Each exception cites the
  Carta record (stakeholder + security details) and the HRIS row it was
  compared against.
- A source-document gap list: every grant missing one or more required
  documents, with the specific missing document named.
- An ambiguous-match list: every name that could not be confidently matched,
  flagged for a human.
- A data-freshness note: the timestamp of the Carta MCP pull and the HRIS
  export date (if available).

## Error handling

- Never edit either system. The skill reads from Carta via MCP and reads the
  HRIS file. It does not write back to Carta or modify the HRIS.
- If the Carta MCP connection drops mid-run, stop and report what was completed.
  Do not use cached or partial data without flagging it.
- Cite the source for every value (the Carta record and the HRIS row). If a
  value is absent or ambiguous, write "not found / unclear -- confirm."
- If a match is ambiguous (name differs, extra space, maiden name, nickname),
  do not assume. Flag it.
- Treat the output like work from a smart intern who is right about 90% of the
  time. Audit it. Read the run carefully the first week.
- The decision stays human. The skill drafts and flags; a person reviews each
  exception and acts in the system of record.

## Eval contract

- **Spec:** A correct run connects to Carta via MCP, pulls stakeholder and
  securities data, parses the HRIS export, and produces a reconciliation report
  that surfaces termination-date mismatches and active-grant-for-terminated-
  employee exceptions ranked by severity, with each exception citing the Carta
  record and the HRIS row, ambiguous name matches flagged rather than assumed,
  and source-document gaps listed. It changes nothing in either system.
- **Rubric** (hard-fail gates in bold):
  1. **Every exception cites the Carta record (stakeholder + security) and the
     HRIS row; an exception with no cite is an automatic fail.**
  2. **No fabricated or inferred values; anything absent or unreadable is marked
     "not found / unclear -- confirm", not guessed.**
  3. Exceptions are ranked by severity tier, not presented as a flat list.
  4. **Every grant is checked for source documents; any grant missing a required
     document appears in the gap list with the specific document named. A
     missing-document grant absent from the gap list is an automatic fail.**
  5. **Neither system is edited; ambiguous name matches are flagged for review,
     never resolved by assumption. Two records that share a name but carry
     different IDs are surfaced as distinct people, never merged.**
  6. **The skill uses Carta MCP tool calls for cap-table data retrieval, not
     file parsing. If the MCP connection is unavailable, the skill stops and
     reports the failure rather than falling back to fabricated data.**
- **Self-tests:**
  - *Termination mismatch + active grant:* A synthetic HRIS file with one
    employee terminated several months ago and a Carta MCP response showing that
    employee with an active grant. A second employee has a termination date that
    differs by months between the two sources. *Output MUST* surface both
    exceptions ranked by severity, each citing the Carta record and the HRIS
    row. *Output MUST NOT* present them as an unranked flat list.
  - *Ambiguous name match:* Carta stakeholder is "Chris Park"; HRIS lists
    "Christopher Park" with no shared ID or email. *Output MUST* flag the pair
    as an ambiguous match for human review. *Output MUST NOT* assume they are
    the same person.
  - *Missing source document:* A grant in Carta is missing a vesting schedule
    while its other documents are present. *Output MUST* surface that grant in
    the source-document gap list, naming the specific missing document.
  - *Same name, different IDs:* Two Carta stakeholders share the name
    "Taylor Reed" but carry different IDs. *Output MUST* surface BOTH as
    distinct people. *Output MUST NOT* merge them.
  - *MCP connection failure:* The Carta MCP server is unreachable. *Output MUST*
    report the connection failure and stop. *Output MUST NOT* fabricate cap-table
    data or silently fall back to an empty dataset.
- **Version:** 1.0.0

## Variant note

This is the Carta MCP-native variant. A platform-agnostic version that works
with any cap-table system via CSV export is available at:
https://skillsandagents.co/skills/equity-reconciliation/

Learn more: https://skillsandagents.co/skills/equity-reconciliation-carta/

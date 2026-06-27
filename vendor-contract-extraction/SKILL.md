---
name: vendor-contract-extraction
description: Extract key terms, risk provisions, cost obligations, renewal/termination clauses, and authorized user counts across a vendor portfolio into one risk-and-cost register. Use to build or refresh a vendor risk and cost inventory.
---
# Vendor Contract Extraction

## What this does
Reads a set of vendor contracts and pulls each one into a single structured register — one row per
vendor — capturing term and renewal dates, notice periods, annual cost and payment terms, the
auto-renew flag, key risk provisions, and authorized user counts. It flags the things that bite you:
auto-renewals whose notice window is open, costs with no cap, and terms it could not find. The output
is one consolidated risk-and-cost register you can act on.

This is the breadth tool. It sweeps the whole portfolio into a structured table. If you instead need
one agreement read deeply into a risk memo, that is a different job — see "When to use it".

## When to use it
- You have a folder of vendor contracts and no single place that says what you owe, when each renews,
  and where the risk sits.
- A renewal or budget cycle is coming and you need a current inventory of cost and notice deadlines.
- You want to refresh an existing register after new contracts came in or terms changed.

Do NOT use this for a deep single-contract review. Reading one agreement clause by clause into a
risk memo is the depth job, and it is a separate skill (`contract-review`). This skill trades depth
for coverage: it is structured and portfolio-wide, not a narrative memo on one document.

## Inputs — how to give it the data
- **Default: drag in the files.** Drop the vendor contract files (PDF, Word, scans) or paste their
  text. A folder of contracts is the normal case here, not the exception — multi-file is expected.
- **Optional: an existing register to update.** Hand over the current register (spreadsheet or CSV)
  and the skill updates rows in place and adds new vendors rather than starting from scratch.
- **Connectors are convenience, not a requirement.** If a contract or spend system is connected
  (e.g. a contract repository, an AP or spend tool like bill.com / Ramp / Sage), it can pull from
  there, but nothing here requires an integration. File drag-in always works.
- **Scanned / OCR'd contracts are provisional.** Numbers and dates read off an image or a noisy OCR
  layer are marked "confirm against source" — they are not treated as clean data until a human checks
  them against the original.
- **One vendor can span several files.** A base agreement plus order forms and amendments is one
  vendor row; note every source file that fed the row.

## Steps
1. Read each contract. For multi-file vendors, read the base agreement and every amendment / order
   form together so later terms override earlier ones.
2. Extract, per vendor, the suggested default field set (confirm or extend this in plan mode — it is
   a starting set, not a hardcode): vendor name; contract term (start/end); renewal type and date;
   notice period to cancel; annual cost; payment terms; auto-renew flag; key risk provisions
   (liability caps, indemnity, data/security, exclusivity, price-escalation); authorized user / seat
   counts; and the source contract + section for each field.
3. Compile into one register, one row per vendor, with a source citation (file + section/clause) for
   every value.
4. Flag the action items: auto-renewals whose notice window is open or about to open, costs with no
   cap or with uncapped escalators, and any term you could not find.
5. Mark each individual value that came from a scanned/OCR'd source as "confirm against source" —
   field by field, not the whole row. If only the cost came off a scan, only the cost is provisional.

## Rules (confirm in the plan)
Surface these in plan mode before the first run and let the operator fill them in. They are the
tacit judgments the skill should not guess.
- **The exact fields the register must carry** — the canonical column set and their order:
- **The renewal-window alert threshold** — how many days before a notice deadline counts as "act now"
  versus "watch":

## Output
One consolidated vendor risk-and-cost register, one row per vendor, each value carrying its source
citation (file + section/clause). The suggested default columns are: vendor; term and renewal dates;
notice period; annual cost; payment terms; auto-renew flag; key risk provisions; authorized user
counts; and the source contract + section per field. This is a starting set the operator confirms or
extends in plan mode, not a fixed schema. A short flag list rides on top: auto-renewals inside their
notice window, uncapped or escalating costs, and missing/ambiguous terms. The register is a draft for
a human to review and act on, not a set of decisions already made.

## Error handling
- **Cite the source for every field.** Each value names its source contract and section/clause. A
  value with no citation does not belong in the register.
- **Flag, do not invent.** If a term is missing or ambiguous, write "not found / unclear — confirm".
  Never infer a notice period, a cost, or a renewal date that the contract does not state.
- **Never silently pass an auto-renewal.** An auto-renewal whose notice window is open or about to
  open is always flagged for human action — the skill does not decide to let it lapse or to cancel.
- **Provisional is field-level, not row-level.** Mark the specific field that came from a scan or a
  noisy OCR layer "confirm against source" — not the whole row. If only the cost came off a scan but
  the renewal date is clean digital text, only the cost is provisional. A row-level warning is too
  coarse; flag the exact value a human needs to recheck.
- **Treat the output like a smart intern's work — about 90% right.** Audit it, especially the flagged
  rows. The decision to renew, renegotiate, or cancel stays with a human.

## Eval contract
- **Spec:** A correct run reads a set of vendor contracts and returns one register, one row per
  vendor, where every extracted value cites its source contract + section, auto-renewals inside their
  notice window are flagged, and missing terms are marked "not found", not guessed.
- **Rubric** (hard-fail gates in bold):
  1. **Every extracted register field cites its source contract + section; a value with no citation
     is an automatic fail.**
  2. **No fabricated values: any term the contract does not state is marked "not found / unclear —
     confirm", never inferred.**
  3. **An auto-renewal whose notice window is open or about to open is flagged, not silently passed.**
  4. The register is one row per vendor with the operator-confirmed field set; multi-file vendors are
     consolidated into a single row that lists every source file AND applies the later term when an
     amendment supersedes the base contract.
  5. The output is a draft register plus a flag list for a human to act on; it does not cancel,
     renew, or commit anything on its own.
  6. **Provisional markers are field-level: a value read from a scan or noisy OCR is marked "confirm
     against source" on THAT field, not as a row-level warning. Marking the whole row provisional
     when only one field came from a scan, or leaving a scan-sourced value unmarked, is a fail.**
- **Self-test:**
  - *Input:* a synthetic two-contract folder, evaluated as of a pinned reference date of
    2026-01-15, where one contract auto-renews on 2026-03-01 with a 60-day cancellation notice
    period (so its notice window is open as of the reference date). *Output MUST* flag that vendor's
    auto-renewal as inside its notice window AND cite the source contract + section for every field
    it filled. *Output MUST NOT* leave the auto-renewal unflagged or list a value without a source
    citation. (The reference date is pinned so this test does not go flaky after publication.)
  - *Input:* a synthetic contract that simply omits any notice period. *Output MUST* mark the notice
    period "not found / unclear — confirm". *Output MUST NOT* invent or infer a notice period.
  - *Input:* a synthetic single vendor spread across two files — a base agreement and a later
    amendment that changes the renewal date and raises the annual cost. *Output MUST* consolidate
    both files into ONE vendor row, apply the LATER term (the amendment's renewal date and cost),
    and cite BOTH source files (the base agreement and the amendment) on the affected fields.
    *Output MUST NOT* emit two separate rows for the one vendor or apply the superseded base-contract
    term.
  - *Input:* a synthetic contract where the annual cost was read off a noisy OCR'd scan while the
    renewal date came from clean digital text. *Output MUST* mark ONLY the cost field provisional
    ("confirm against source") and leave the cleanly-sourced renewal date unmarked. *Output MUST NOT*
    mark the whole row provisional or leave the scan-sourced cost unmarked.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/vendor-contract-extraction/

---
name: contract-review
description: Review a vendor, customer, payor, or partner contract before sign-off. Extracts key terms with clause citations, flags risks and cost obligations ranked by severity, notes what's missing versus a standard contract of its type, and drafts a decision-maker (CFO/GC) memo. Use when a new or renewing contract needs analysis before signing.
---

# Contract Review

## What this does
Turns a contract you're about to sign or renew into three things a decision-maker can act on: a cited terms table, a ranked risk list, and a short memo. It accelerates the read; it does not make the decision. Every extracted term cites its clause so you can verify, and anything missing or ambiguous is flagged rather than guessed.

## When to use it
A new or renewing contract needs a risk read before sign-off — a vendor agreement, a customer or payor contract, an MSA, an SOW, a renewal, or an amendment.

## Inputs — how to give it the agreement
- **The contract itself.** Drag in the PDF or DOCX, or paste the text.
- **If the agreement is several documents** (a base agreement plus amendments, exhibits, schedules, or order forms), give it all of them and say which is which. Terms in an amendment override the base, so the skill needs the full set and reconciles overrides — it will not analyze one file in isolation and call it done.
- **If the contract is a scanned image or photographed PDF, say so.** Text extraction from scans is lossy; the skill works from the OCR'd text but treats every number and date as "confirm against the source," not authoritative.
- **Optional context:** the deal model or rate assumptions, your benchmark for this counterparty type, or a prior/comparable contract to diff against.
- **If a connector is wired up** (Google Drive, a CLM / contract repository, email): the skill can pull the file, but the analysis is identical to an uploaded one. The connector is convenience, not a requirement.

## Steps
1. Read the contract — and every amendment and exhibit — end to end before extracting anything.
2. Extract key terms into a table, **citing the section (and page where available) for every term**: counterparty, effective and termination dates, renewal / auto-renew terms, notice periods, pricing / rate structure, any guarantee or performance provisions (e.g., MLR, SLA, uptime, or volume guarantees), risk-share / reinsurance terms where present, payment terms, caps and floors, exclusivity, liability / indemnity, data and compliance obligations, and authorized-user counts (for vendor/SaaS contracts). If a term isn't present, write "not found" — do not infer it.
3. Flag risks: anything off-market, one-sided, ambiguous, auto-renewing without notice, uncapped, or that creates a cost the reviewer should price. Rank each high / medium / low with the clause cited and a one-line reason.
4. Note what's missing or unclear versus a standard contract of this type.
5. Draft a memo: a one-paragraph summary, the key economics, the top 3–5 risks each with a recommendation, and the open questions to take back to the counterparty.

## Rules (confirm in the plan before first run)
These are the tacit judgments only the reviewer holds. Fill them in once, in plan mode, and the skill applies them every run:
- What "off-market" looks like for this counterparty type: [your benchmark].
- Return threshold / hurdle the economics must clear: [____].
- Guarantee thresholds that matter for this contract type (e.g., MLR, SLA, uptime, volume): [____].
- Deal-breaker clauses vs. negotiable ones: [____].

## Output
A cited terms table + a ranked risk list (severity, clause cite, recommendation) + a memo draft. Markdown, exportable to .docx.

## Error handling
- **Cite or flag — never infer.** Every extracted term cites its clause. If a term is absent or ambiguous, mark it "not found / unclear — confirm"; never assume a standard term is present or invent a number.
- **Scanned / OCR'd input:** treat extracted numbers and dates as provisional and tell the reviewer to confirm them against the source.
- **The decision stays human.** The skill drafts the analysis and the memo; it does not approve, sign, or negotiate. Roughly half of a real contract review is judgment — the skill hands you a faster read, not a verdict.

## Eval contract
- **Spec:** A correct run produces a terms table where every row cites a section, a risk list ranked by severity with each item tied to a clause, an explicit "missing / unclear" list, and a memo a CFO or GC could forward. No invented terms or numbers.
- **Rubric** (hard-fail gates in bold):
  1. **Every extracted term cites a clause/section. A term stated without a cite is an automatic fail.**
  2. **No fabricated terms or numbers. Anything not in the document is marked "not found," not inferred.**
  3. Risks are ranked (high / med / low) with a reason and a cite, not a flat list.
  4. Amendments and exhibits, when provided, are reconciled (overrides reflected), not analyzed in isolation.
  5. The memo states the economics and the open questions, and recommends — without deciding.
- **Self-test:**
  - *Input:* a one-page MSA with an auto-renew clause and a 90-day notice window. *Output MUST* flag the auto-renew as a risk with the clause cited and surface the notice deadline. *Output MUST NOT* state a renewal price that isn't in the document.
  - *Input:* a contract with the payment term left blank. *Output MUST* list payment terms as "not found — confirm." *Output MUST NOT* fill in "Net 30" or any default.
  - *Input:* a base agreement that sets a 36-month term plus a later amendment that changes the term to 12 months. *Output MUST* reconcile the two and report the 12-month term (the amendment overrides the base), citing the amendment clause. *Output MUST NOT* report the base 36-month term as if the amendment did not exist, or analyze the two documents in isolation.
  - *Input:* a generic SaaS subscription agreement (seat-based pricing, an auto-renew clause, and a uncapped liability section) with no healthcare or payor terms. *Output MUST* extract the seat count and pricing with clause cites and flag the uncapped liability as a risk. *Output MUST NOT* assume an MLR, payor, or reinsurance frame that isn't in the document.
- **Version:** 1.0.0

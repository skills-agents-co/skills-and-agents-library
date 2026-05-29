---
name: buy-side-diligence
description: Runs systematic buy-side due diligence on a private company acquisition target. Deconstructs financials into normalized earnings, stress-tests the seller's narrative, cross-references documents to surface inconsistencies, quantifies red flags into valuation adjustments, and produces an investment-committee-ready output package. Built for corporate development teams, PE associates, search fund operators, and M&A advisors running buy-side diligence. Use whenever the user says "run diligence", "due diligence", "DD this", "QoE this", "build a red flag matrix", "normalize this EBITDA", "diligence package", "/diligence", or points at a data room, CIM, or financial package and asks what's wrong with it.
---

# Buy-Side Due Diligence

Systematic buy-side due diligence on a private company target. Private company acquisitions are information-asymmetry warfare: the seller spent years curating the story, and you have weeks to punch holes in it. This skill processes the data room at a speed and depth a manual team can't match, and turns every finding into a price adjustment, a deal protection, or a walk recommendation.

It produces a full output package: normalized EBITDA bridge, balance sheet stress test, working capital peg, customer concentration map, legal exposure summary, document-inconsistency findings, a prioritized red-flag matrix, a valuation impact, and an IC memo.

## The prompt library is the engine

The staged prompt library lives at `references/prompt-library.md` (relative to this skill). Read it at the start of every run. It contains:

- **Layer 1**, a context-setter to run first; every later prompt inherits its framing.
- **Stage 1 (A-C)**, pre-LOI screening from the CIM.
- **Stage 2 (1-12)**, post-LOI financial, commercial, operational, and legal analysis.
- **Stage 2 (13-15)**, cross-referencing: document inconsistency, narrative validation, bear case.
- **Stage 3 (D-F, 16-18)**, deal structuring: red-flag matrix, valuation impact, integration plan.
- **Stage 4 (G-L)**, investment committee outputs.

Use the prompts as written. They are calibrated to surface the risks most common in private company transactions.

## How to use it

1. **Frame the deal.** Fill the Layer 1 context-setter with industry, company description, revenue, adjusted EBITDA, asking price, and implied multiple. Keep that framing active for the whole session.
2. **Map the data room and log what's missing.** Tier every document: Financial / Commercial / Operational / Legal. Then list what the seller did NOT provide. Unexplained absences (no environmental records for a manufacturer, no HR claims history for a large headcount) are findings in their own right. Maintain a missing-document log.
3. **Run the stage prompts** against the documents available, in order. Paste the relevant documents before each prompt. Build every analysis independently from the raw financials first, then compare against the seller's add-back schedule, do not anchor on the seller's version.
4. **Synthesize last, with everything loaded.** Run cross-referencing (13-15), then the red-flag matrix (16), valuation impact (17), and integration plan (18). The bear case (15) runs last. Every red flag must carry a quantified dollar impact.
5. **Produce the output package** (format below).

## Architecture note: centralize the reasoning

The strongest analytical edge is cross-referencing every document against every other one (Prompts 13-15). That depends on shared context. So:

- For a small target that fits one context, run everything in a single thread.
- For a large data room, you can split the *reading* across separate passes (one per document tier) to extract structured findings, but the cross-referencing, bear case, and synthesis must run once, with all findings together. Never split the synthesis: isolated passes are blind to each other, which defeats the cross-reference advantage.

## Output package format

```markdown
# Diligence, [Target], [Date]

## Deal frame
[Industry, size, price, multiple, thesis]

## Missing-document log
[What the seller did not provide and what each absence implies]

## Normalized EBITDA bridge
[Adjustments, each with a High/Medium/Low confidence rating and a dollar amount]

## Balance sheet & hidden liabilities
[Asset quality; off-balance-sheet and contingent liabilities]

## Working capital peg
[Recommended target range; pre-close manipulation flags]

## Commercial
[Customer concentration; change-of-control exposure; pipeline quality]

## Operational & legal
[Key-person risk; IT; contract risk map; legal exposure]

## Document inconsistencies
[Book vs tax; payroll vs filings; CIM vs financials]

## Bear case
[The strongest case against the deal]

## Red flag matrix
| Issue | Rating (Critical/High/Medium/Low) | $ Impact | Recommended protection | Specialist needed |
|---|---|---|---|---|

## Valuation impact
[Adjusted EBITDA; revised range; structure to protect the buyer]

## Verdict & conditions
[Go / no-go and the specific conditions to proceed]
```

## Pitfalls

- This is an analytical accelerator, not a replacement for a sell-side QoE report or an accountant's sign-off on adjusted earnings. State that in the output.
- Use clean digital exports. OCR errors in scanned financials cascade into analytical errors.
- Feed monthly management accounts where possible, not just annual statements, monthly data exposes seasonality games and pre-close working capital manipulation that annual numbers hide.
- Don't anchor on the seller's add-back schedule. Build the bridge independently, then compare.
- The bear case underperforms if run early. Run it last, with full context.
- A red flag without a quantified dollar impact will not move an investment committee.
- Run each deal in its own session. Blending two targets degrades output and creates confidentiality risk.

---

*Methodology adapted from the buy-side due diligence operating system circulated on the SearchFunder forum. This skill is an analytical aid; it does not constitute accounting, legal, or investment advice.*

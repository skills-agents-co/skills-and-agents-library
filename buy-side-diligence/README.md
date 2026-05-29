# Buy-Side Due Diligence (Claude Skill)

A Claude skill that runs systematic buy-side due diligence on a private company acquisition target. It deconstructs financials into normalized earnings, stress-tests the seller's narrative, cross-references documents to surface inconsistencies, quantifies red flags into valuation adjustments, and produces an investment-committee-ready output package.

Built for corporate development teams, PE associates and principals, search fund operators, strategic acquirers, and M&A advisors.

## What's in here

```
buy-side-diligence/
├── SKILL.md                      # the skill: methodology, workflow, output format
└── references/
    └── prompt-library.md         # the 30-prompt staged library (Layers 1-4)
```

## How to install

**Claude Code / Agent SDK:** drop the `buy-side-diligence/` folder into your skills directory (e.g. `~/.claude/skills/`). It loads automatically and triggers on diligence-related requests.

**claude.ai / manual use:** open `references/prompt-library.md` and run the prompts in order in a single conversation thread. Start with the Layer 1 context-setter, paste documents before each analysis prompt, and run the cross-referencing and synthesis prompts last.

## How to use

1. Frame the deal with the Layer 1 context-setter (industry, size, price, multiple).
2. Map the data room into four tiers and log what the seller did NOT provide.
3. Run the stage prompts against the documents, building each analysis from the raw financials before comparing to the seller's add-back schedule.
4. Synthesize last, with everything loaded: cross-reference, red-flag matrix, valuation impact, IC memo. Run the bear case last.

## A note on scale

The skill's biggest analytical edge is cross-referencing every document against every other one. That depends on shared context, so the synthesis must always run as a single pass with all findings loaded. For a large data room you can split the *reading* across passes (one per document tier) to extract findings, but never split the synthesis.

## Disclaimer

This skill is an analytical accelerator, not a replacement for a sell-side quality-of-earnings report or an accountant's sign-off on adjusted earnings. It does not constitute accounting, legal, or investment advice. Methodology adapted from the buy-side due diligence operating system circulated on the SearchFunder forum.

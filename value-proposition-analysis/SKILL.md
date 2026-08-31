---
name: value-proposition-analysis
description: Takes a company's stated features and a target market segment and writes a five-part sales-enablement analysis, pain points solved, feature advantages, customer support benefits, integration capabilities, and ROI potential. Every pain point and feature advantage traces back to a feature you actually gave it, and it asks for what's missing instead of making features up. Use whenever you say "analyze our value proposition", "how do our features solve [segment]'s problems", "write a value prop for sales", "/value-proposition-analysis", or hand it a feature list plus a target market and ask what to tell a prospect.
author: "Skills and Agents Co"
version: "1.0.0"
installType: simple
requiresMCP: false
mcpDependencies: []
triggerPhrases:
  - "analyze our value proposition"
  - "how do our features solve [segment]'s problems"
  - "write a value prop for sales"
  - "/value-proposition-analysis"
status: published
---

# Value Proposition Analysis

## What this does

Takes a list of a company's actual features and a target market segment,
and turns them into a value proposition analysis a sales person can use in
a conversation or a deck. The output has five sections: pain points solved,
feature advantages, customer support benefits, integration capabilities,
and ROI potential.

Every pain point and feature advantage in the output has to trace back to a
feature you actually supplied. If a feature list is thin or a segment is
missing, this skill says so and asks for what it needs, instead of
inventing a feature that sounds plausible. The ROI section always says what
an estimate is based on (time, cost, error rate, or something similar), it
never states a bare number with nothing behind it.

## When to use it

Use this when you have a company's features in hand and a market segment
you're selling into, and you want a sales-ready breakdown of why those
features matter to that segment. Good for prepping a sales call, writing
talk track for a rep, or building the value-prop section of a deck.

This skill does no live web search and no competitor research. It works
only from what you give it, plus the starter segment patterns in
`references/segment-challenge-patterns.md`. If you want research on a
competitor's positioning, use a different skill for that.

## Inputs

1. **The company's features.** A list of what the product actually does.
   Bullet points, a paragraph, a feature sheet, whatever you have.
2. **The target market segment.** Who you're selling into: SMB, mid-market,
   enterprise, a vertical like fintech or healthcare, or your own segment
   name.

**Either one missing.** Ask for it before writing anything. Don't guess a
company's features and don't guess a target segment. A value prop built on
a guessed feature or a guessed segment isn't one a rep can stand behind in
a room.

## Steps

1. Confirm you have both inputs. If the features or the segment are
   missing, ask for them and stop here.
2. Read `references/segment-challenge-patterns.md` and look for the
   supplied segment or something close to it. If it's there, use its pain
   points as a starting list. If the segment isn't a close match to
   anything in the file, don't guess: ask the user directly what that
   segment's biggest challenges are, and use their answer instead.
3. **Pain points solved.** Build the pain point list from three sanctioned
   sources only: the reference table's pain points for this segment, what
   the user told you directly, or a pain point directly implied by a
   feature the user actually supplied (for example, a feature that
   "auto-matches invoices" directly implies the pain point "manual invoice
   matching"). For each pain point, name the specific feature that
   addresses it. If a reference-table or user-stated pain point has no
   matching feature, don't drop it silently: list it anyway and mark it
   "No supplied feature addresses this," per the Output format below, so
   the gap is visible rather than hidden.
4. **Feature advantages.** For each feature the user supplied, state what
   it lets the customer do that they couldn't do as well before, in plain
   terms a buyer would understand. Every advantage listed here must name
   the feature it comes from. Do not add a feature that wasn't supplied,
   even if it would make the story cleaner.
5. **Customer support benefits.** State how the features reduce support
   burden or support cost, for the buyer's team or for their own
   customers, if support benefits are visible: fewer manual steps, fewer
   error-prone workflows, self-service capability, and so on. If nothing
   in the supplied features touches support, say that directly rather than
   inventing a benefit.
6. **Integration capabilities.** State what the features say about how the
   product fits into the segment's existing tools and workflows. Only
   describe integrations the supplied features actually mention or clearly
   imply. If integration isn't addressed by anything supplied, say the
   input doesn't cover it rather than assuming compatibility.
7. **ROI potential.** For each concrete benefit above, translate it into a
   basis for return: time saved, cost avoided, error rate reduced, or
   something similar. State the basis every time. Never state a bare
   percentage or dollar figure with no stated basis. If you don't have
   enough information to estimate a basis, say that plainly instead of
   making one up.
8. Write the output using the format below.

## Output format

```markdown
# Value Proposition Analysis: <company or product name>

**Target segment:** <segment>

## Pain points solved
- <pain point>, solved by <feature>.
...or: "No supplied feature addresses <pain point> for this segment."

## Feature advantages
- <feature>: <what it lets the customer do now>.

## Customer support benefits
- <benefit>, from <feature>.
...or: "The supplied features don't say anything about support burden."

## Integration capabilities
- <integration>, from <feature>.
...or: "The supplied features don't cover integration for this segment."

## ROI potential
- <benefit>: estimated return based on <time saved | cost avoided | error
  rate reduced | other stated basis>.
```

## Pitfalls

- **Don't invent a feature to fill out a section.** If a section would be
  thin, say it's thin. A rep who gets caught citing a feature that doesn't
  exist loses the deal and the skill's trust.
- **Don't state an ROI number with no basis.** "Saves 30%" means nothing
  without "of what, based on what." Always name the basis.
- **Don't fill customer support or integration from guesswork.** If the
  features don't say anything about either, say so instead of assuming.
- **Don't treat the segment reference table as exhaustive.** It's a
  starting point. When the user's segment isn't a close match, ask them
  directly instead of forcing a fit.

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/value-proposition-analysis/).

## Eval Contract

### Spec

A correct run takes a company's stated features and a target market
segment and produces one analysis with five sections, in this order: pain
points solved, feature advantages, customer support benefits, integration
capabilities, ROI potential. Every pain point and feature advantage in the
output names a feature the user actually supplied. Nothing in the output
names a feature that wasn't given. Every ROI figure states its basis (time,
cost, error rate, or similar); no bare number appears with no basis
attached. When the features or the segment are missing at the start, the
skill asks for them instead of guessing. When a section has nothing to
say, the output states that plainly instead of inventing content to fill
the section.

### Rubric

Score each dimension 0 or 1, total out of 6. Run the hard-fail gate first.

**Hard-fail gate (check before scoring):** Any ROI figure with no stated
basis, or any feature named in the output that the user did not supply, is
an automatic fail, regardless of total score. A number with no basis or a
feature that doesn't exist is the kind of detail a sales rep repeats to a
prospect, and it breaks trust the moment it's checked.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Five sections present, in order | All five sections appear, in the order pain points, feature advantages, support, integration, ROI | A section is missing, renamed, or out of order | 1 |
| 2 | Pain points sourced correctly | Every pain point comes from the reference table, the user's own words, or a feature-implied pain point, and any unaddressed one is explicitly marked "no supplied feature addresses this" rather than dropped | A pain point is dropped silently, or one appears that traces to none of the three sanctioned sources | 1 |
| 3 | Feature advantages trace to supplied features | Every feature advantage names a feature the user supplied | A feature advantage names a feature not in the input | 1 |
| 4 | ROI basis stated | Every ROI line states its basis (time, cost, error rate, or similar) | Any ROI line states a number with no basis (also covered by the gate) | 1 |
| 5 | Missing-input handling | When features or segment are missing, the skill asks for them before producing output | The skill produces an analysis despite a missing input | 1 |
| 6 | Empty-section honesty | A section with nothing to support it says so directly | A section is filled with a plausible-sounding but unsupported claim | 1 |

**Score to action:** 6/6 ship. 4 to 5 acceptable, note the gap. 2 to 3
borderline, flag for human review. 0 to 1 bad, root-cause. Any hard-fail
gate trip is fail regardless of total.

### Self-Test

**Scenario A, the traceability test.**

Features supplied: "Automated invoice matching. Real-time spend
dashboards." Segment: mid-market.

- The output MUST list a pain point tied to manual invoice reconciliation,
  citing automated invoice matching as the feature that solves it.
- The output MUST NOT name any feature in the pain points or feature
  advantages sections other than automated invoice matching and real-time
  spend dashboards.
- Every ROI line MUST state a basis (for example time saved reconciling
  invoices, or fewer manual errors). The output MUST NOT state a bare
  percentage or dollar figure with no stated basis.
- If the supplied features say nothing about customer support or
  integration, the output MUST say so directly in those sections rather
  than inventing a benefit or an integration.

**Scenario B, the missing-input test.**

Only a segment is supplied: "enterprise." No features are given.

- The output MUST NOT produce a five-section analysis. It MUST ask for the
  company's features before proceeding.
- The output MUST NOT invent a plausible-sounding feature list to fill the
  gap.
- Once features are supplied in a follow-up, the same tracing rules from
  Scenario A apply: no feature appears in the output that wasn't in the
  follow-up list.

### Version

1.0.0

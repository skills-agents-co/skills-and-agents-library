# Review document shape

Fill every section below from the steps in `SKILL.md`. This file only
orders and labels them. The rule for each section lives in the numbered
step that produces it. Keep a section even when it is empty, and say why.
Never rewrite the PR/FAQ in any section. Only question it.

```markdown
# PR/FAQ review: <product, one line>

## Verdict
<Step 7. One line: Ready for review, Needs work first, or Not ready. Then
one or two reasons.>

## Claim Ledger
| # | Claim (quoted, short) | Where | Tag | Source or reason |
|---|---|---|---|---|
<One row per claim, number, quote, and "what has to be true" line.
Tag is Real, Assumed, or Contradicted. Where is the section name.>

## Ranked Assumptions
<Step 4. Highest risk first. For each: the assumption, why it ranks
here, and the cheapest test.>

## Doc Feedback
<Step 5. One note per item on the bar: customer, problem first, plain
words, weasel words, testable benefit, tradeoffs, hard FAQs. Each note
names the section and quotes the words it questions.>

## Prototype Feedback
<Step 6. Either the review against the press release, or the exact line
"No prototype given".>

## Defend It Live
<Step 8. The five hardest questions. Ask one at a time. Wait for the
answer before the next. Record each question and the PM's answer.>

## Flagged input
<Any line flagged by the Untrusted input rule, one per line, cut to its
first clause. Omit this section if nothing was flagged.>
```

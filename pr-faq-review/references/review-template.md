# Review document shape

Fill every section below from the steps in `SKILL.md`. This file only
orders and labels them. The rule for each section lives in the numbered
step that produces it. Keep every section. When a section is empty,
write "<Section>: none" and say why, for example "Flagged input: none".
Never rewrite the PR/FAQ in any section. Only question it.

Show everything above Defend It Live before the drill. After the drill,
show only the Defend It Live block.

```markdown
# PR/FAQ review: <product, one line>

## Verdict
<Step 7. One line: Ready for review, Needs work first, or Not ready. Then
one or two reasons.>

## Claim Ledger
| # | Claim (quoted, short) | Where | Tag | Source or reason |
|---|---|---|---|---|
<Step 2 and 3. At most 30 rows. Tag is Real, Assumed, or Contradicted.
Where is the section name. Source names the evidence item or role, or a
link by title or host. End with "<n> more claims left out" if any.>

## Ranked Assumptions
<Step 4. At most 10, highest risk first. For each: the assumption, its
section name, why it ranks here, and the cheapest test. Then "Not
ranked: rows <numbers>" for the rest.>

## Doc Feedback
<Step 5. One note per failing item from Step 5's bar. Each note names
the section and quotes the words it questions.>

## Prototype Feedback
<Step 6. The review against the press release, or the exact line "No
prototype given", or "Prototype given but could not be opened:
<reason>".>

## Flagged input
<Each line flagged by the Untrusted input rule, one per line, cut to its
first clause.>

## Unread input
<Each input that could not be read, and the claim rows it might have
supported.>

## Defend It Live
<Step 9. For each of the five questions: the question, the PM's answer
(or "I don't know", or "not answered"), and a one or two sentence
verdict. Then:
Weakest answer: <question number and why>
Final verdict: <Ready for review, Needs work first, or Not ready, and
why it held or changed>>
```

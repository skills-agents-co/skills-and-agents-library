# Matching Mechanics

Detail for Step 4, matching the bank side against the QBO side. The four
classification labels and the duplicate-candidate rule live in the
SKILL.md body, not here.

## Normalize Signs First

**Normalize how each side signs a withdrawal and a deposit, before you
compare amounts.** An uploaded statement can encode a withdrawal as a
negative number. It can also split debits and credits into separate
columns. QBO's register may use a different convention. A direct
comparison of the raw captured amounts can classify every withdrawal as an
amount mismatch. That happens even when the two transactions are
identical.
`financial-pulse`'s own pattern normalizes this first. Do the same here.
Resolve both sides to one consistent signed representation, or to one
consistent debit and credit label. Do that before you apply the
amount-equality check below.

## The Three-Criteria Match Test

Look for a QBO register line for every bank-side transaction. The register
line must meet all three of these:

- **Amount** matches exactly, on the normalized direction-consistent
  values from above
- **Payee** matches. Allow reasonable normalization, such as "AMEX
  EPAYMENT" against "American Express". Never guess across genuinely
  different payees.
- **Date** falls inside the resolved tolerance window of the bank-side
  date

## Reverse Direction

Do the same in reverse for a QBO register line with no bank-side
counterpart. Those lines are also missing counterparts, from the other
direction.

## Confidence Tiers

A same-day, same-amount, same-payee match is the highest-confidence
tier — this is what `references/output-templates.md`'s Confidence column
calls "Highest." A match that clears all three criteria only because the
date falls inside the tolerance window, rather than landing same-day, is
"Within window" — real, but worth a closer look from the bookkeeper
before approving it.

# Matching Rules: Step 4's One-to-One Match and Aging Cross-Check

(See body Step 4 for the one-to-one invariant — every document matches at
most one bill, every bill matches at most one document, with a competing
match flagged in Step 5 rather than resolved — and for the
period-activity-population scope this procedure works from.) That
invariant holds even when both bills share the same vendor, amount, and
date. That case happens. Duplicate-looking bills from one vendor, on one
day, for one amount are common. A one-to-one rule has to get them right,
which is what the two passes below do.

**Resolve forced assignments first, before you claim anything. Then check
the remaining ties in both directions.** A pairwise "is my sole candidate
contested" test on its own over-flags real matches as ambiguous. Consider
bill A, whose only candidate is document X. Consider bill B, which could
match either X or Y. Judged pairwise, B contests A's sole candidate X. So
both A and B would get marked ambiguous. But A→X and B→Y is the one
consistent assignment. Forcing it through first is the correct result, not
an arbitrary one. So work in two passes, not one.

**Pass 1: build every bill's full candidate set, then resolve forced
assignments to a fixed point:**

1. Find every unclaimed Step 3 source document for every bill in Step 2's
   period-activity population. A candidate document has the same vendor
   and a matching or close amount. Its currency is compatible with the
   bill's currency, or reconcilable to it. Its date falls within the
   period, or within a reasonable window around the bill date. Those
   documents are the bill's candidate set.
2. Repeat the following until nothing changes in a full pass. A bill with
   exactly one candidate remaining claims it **only if no other unresolved
   bill also holds that same document as its own sole remaining
   candidate**. Classify the bill **Matched** when the claim goes through.
   Then remove that document from every other bill's candidate set.
   Removing a document can leave another bill with exactly one candidate
   too. That is why this repeats to a fixed point rather than running
   once.

   **Check the document side before every claim. A sole candidate is
   forced only if it is forced for exactly one bill.** Document X is
   genuinely contested if two bills each hold it as their sole remaining
   candidate. Neither bill may claim it. An award by evaluation order to
   whichever bill runs first would starve the other. It would report a
   real receipt as missing. Leave both bills unresolved. Let Pass 2
   classify them **Ambiguous match**, and list X as the competing
   candidate under each. The same rule covers any group of three or more
   bills whose sole candidates collide on one document.

   Iteration bound: this loop can claim at most one document per bill. So
   it always reaches a fixed point within as many full passes as there are
   bills. Stop iterating if it has not settled after that many passes.
   Send everything still unresolved to Pass 2 as Ambiguous match, rather
   than looping further.

**Pass 2: whatever is left after Pass 1 stops changing is genuinely
ambiguous, not merely provisionally contested:**

3. Classify each bill still holding more than one candidate as **Ambiguous
   match**. List every remaining competing candidate in Step 5, so the
   bookkeeper decides. This is now a real ambiguity, because forced
   assignments already claimed everything they could.
4. Take each bill still holding exactly one candidate that another
   still-ambiguous bill also lists. Both bills share that document as a
   genuine competing candidate. Report both in Step 5, rather than letting
   evaluation order pick a winner. This case is rarer after Pass 1's
   fixed-point resolution. It can still occur with a cycle of three or
   more mutually competing bills.
5. Classify a bill with zero candidates remaining as **Unmatched**.

Process bills in a stable order. Sort by bill date, then by bill
reference. A rerun over the same data then produces the same matches.
Never rely on whatever order the MCP happens to return rows in.

Do this for every Step 3 source document that Pass 1 did not already
claim:

1. Look for a bill from Step 2's period-activity population that it could
   match.
2. Classify the document:
   - **Matched**: a bill match above already claimed it
   - **Contested**: it is one of the competing candidates listed under an
     Ambiguous-match bill in Step 5. Do not also mark it Unmatched below,
     because Step 5 already accounts for it.
   - **Unmatched**: no corresponding bill exists among Step 2's
     period-activity population at all. That population is not "open
     bills". A document that backs a bill fully paid within the period has
     a real bill to match against. That bill will not appear in Step 4's
     aging total.

## Computing the Payable Total

**Every bill in Step 2's aging population with a genuine open balance
stays in the payable total, with no exceptions. That includes an
ambiguous-match bill and a currency-mismatched bill.** The dollar amount
that enters the total is the bill's **open balance as of the cutoff**.
That balance is the bill's original amount, less the applied payments and
credits. Step 2's capture holds those applications. It is never the bill's
original face amount. A $10,000 bill with $6,000 already applied
contributes $4,000 to the total, not $10,000. The face amount here would
overstate AP. It would manufacture a false discrepancy against QBO's own
AP Aging report. That report already gives open balances, not face
amounts.

A missing, ambiguous, or foreign-currency backing document changes nothing
about the open-balance figure itself. Exclude a bill from the total in one
case only. You must have a specific reason to believe that it is not a
real payable. Two such reasons are a duplicate of another bill already
counted, and the bookkeeper saying so directly. Documentation status by
itself is never that reason.

Two narrow exceptions exist. A bill whose amount genuinely cannot be
converted to home currency gets excluded, and flagged explicitly as
"amount unknown". That case means no exchange rate and no home-currency
equivalent are available from QBO at all. Take a bill covered by a
multi-bill payment or vendor credit whose per-bill allocation the MCP does
not expose. Step 2's fallback excludes it, and flags it as "allocation
unavailable". Neither exception is a documentation-missing exclusion.

**Net each vendor credit's remaining unapplied portion against the total.
Never net its face amount.** An unapplied balance is a real negative
payable, the same way QBO's own AP Aging balance treats it. So include it
as a negative amount alongside the open bills. Do not report the gross
bill total alone. A credit's *applied* portion already shows in the
reduced open balance of its bill. Step 2's capture records that.
Subtracting the credit's face amount here as well would count that portion
twice, and would understate AP. A credit with no remaining unapplied
balance contributes nothing to this total. It matters only for the bill
balances that it already reduced.

A vendor credit has no due date, so it gets no aging bucket of its own.
Give it its own row in the bucket view instead. Show the vendor and a
negative amount in whichever column represents "current", because a
credit is not past due. The credit is then visible in the vendor-level
breakdown, rather than folded silently into the grand total.

Every real bill and credit counts here, whatever its matching or
documentation status. So this **credit-netted** total is directly
comparable to QBO's own AP Aging report, which is itself credit-netted.
Documentation status never moves this number. So documentation status is
never the reason for a gap.

**But the comparison is clean only when nothing was excluded.** This skill
makes two exclusions. One is a bill with no determinable home-currency
amount. The other is a bill covered by a multi-bill payment or credit
whose per-bill allocation the MCP does not expose. Both are absent from
this skill's total and present in QBO's. So this total is *expected* to
come in under QBO's report when any exclusion fired. The shortfall is
roughly the excluded bills' amounts. Reporting that expected gap as a
discrepancy would be a guaranteed false positive on every run with an
exclusion.

Read it this way:

- **No exclusions this run** → the two totals should match. Any gap is a
  genuine discrepancy worth investigating.
- **One or more exclusions** → say plainly that N bills are excluded here
  and included in QBO's figure. So a gap of roughly that size is expected,
  not a finding. Flag the gap as a genuine discrepancy in one case only.
  It must be clearly larger or smaller than the excluded items explain.
  The whole reason for excluding these bills is that no reliable amount
  exists for them. So this is a judgment about order of magnitude, not an
  exact subtraction. Say that plainly. Do not imply a precise
  reconciliation.

State this aging view's total against the **AP Aging** report pulled in
Step 2. Flag the discrepancy if your bill-level reconciliation and QBO's
own report disagree. Never silently adopt one number over the other.

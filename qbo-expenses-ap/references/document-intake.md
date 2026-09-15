# Document Intake: Step 3's Validation Rules

**Ask for documents that cover every bill in Step 2's period-activity
population. Do not ask only about bills still open at the cutoff.** A bill
fully paid within the period still needs its source document matched in
Step 4. An ask restricted to "open" bills would leave that document with
nothing to match against.

This skill does not parse a photo, a scan, or a PDF. It works from
bookkeeper-entered summary data only.

**Validate every row before it reaches Step 4's matching.** There are two
different outcomes here. Never collapse them.

**Flag the row and exclude it from matching** when there is nothing usable
to match on. That covers a row missing a vendor, a date, or an amount. It
covers a non-numeric or unparseable amount. It covers a negative amount,
which is a signed adjustment rather than a real receipt: flag it, and
never silently flip the sign. It covers a date that does not parse. It
covers a date clearly outside any reasonable window around the stated
period. Flag and exclude a row missing its currency too, if this company
has multicurrency enabled. Step 4's currency-compatibility check cannot
run without the currency.

**Flag the row and still match it** when the row is usable and merely
looks suspicious. That covers a row that appears to duplicate another row
already in the list. **Never exclude a suspected duplicate from
matching.** Two legitimate invoices from the same vendor, on the same
date, for the same amount are common. That is exactly the case that Step
4's one-to-one rule exists to handle correctly. Excluding the second row
removes a genuine receipt from the candidate pool, and falsely reports its
bill as missing documentation. That is a worse error than a duplicate flag
that the bookkeeper can dismiss. So flag the row in Step 5 as a possible
duplicate. Leave it in the candidate pool. Let one-to-one matching sort
out which bill each row backs.

**Compare every identifying field that the bookkeeper supplied when you
decide whether two rows even look like duplicates.** Do not compare only
the vendor, the date, and the amount. The description, the currency, and
any invoice or document reference in the paste all count. Two rows that
differ in any supplied field are different documents, and get no duplicate
flag at all. Reserve the flag for rows identical across everything
provided.

A row flagged either way still lands somewhere in the final output. See
Step 5's flag list.

---
name: invoice-generation
description: Draft a customer invoice from billing inputs -- customer, line items, terms -- with every amount cited to an input and nothing invented. Use to generate the invoice you send to a customer for work done or goods delivered, not to process invoices you receive.
---
# Invoice Generation

## What this does
Handles the clerical front end of accounts receivable. It takes the billing inputs for a job or
period -- who is being billed, what for, and on what terms -- and drafts a plain, itemized invoice:
invoice number, invoice date, due date, line items with quantity and rate, and a total. It never
sends the invoice, never marks it paid, and never posts it to an accounting system. A person reviews
the draft and sends it.

Treat it like a sharp intern drafting the paperwork: fast on the boring parts, always cited, always
handed back for a human to check before it goes out the door.

## When to use it
- You bill customers for work done, hours logged, or goods delivered and someone currently
  builds the invoice by hand from a time sheet, order, or contract.
- You want the drafting -- numbering, line items, math, due date -- automated but sending the
  invoice and recording the payment kept human.
- Run it per job, per customer, or on a billing-cycle schedule (e.g. end of month).

Do not use it to send an invoice, record a payment, or post to an accounting system. It drafts; a
human sends. This is the accounts-receivable counterpart to `ap-invoice-processing`, which handles
invoices coming in -- this one handles invoices going out.

## Inputs -- how to give it the data
Default inputs, no special tooling required:
- **The customer.** Name, billing contact, and billing address if you invoice on letterhead.
- **The line items.** For each item: description, quantity, and rate (or a flat amount). Give it a
  time sheet, a signed order, a contract, or just the numbers in chat.
- **The payment terms.** When the invoice is due (e.g. net 30, due on receipt), and any deposit or
  prior payment to net against the total.
- **The invoice number.** Either a number to use, or enough of your prior invoices/log to derive the
  next one in sequence.

Handling notes:
- **Missing or ambiguous rate.** If a line item has no rate given, or two sources disagree on the
  rate, do not pick one -- flag it "uncertain, needs confirmation" and leave it out of the total
  until confirmed.
- **Quantity vs. flat fee.** Some line items are quantity x rate, others are a flat amount. Use
  whichever the input actually gives; do not compute a rate that was never stated.
- **Multiple jobs for one customer in a period.** Treat each as its own line item (or its own
  invoice, per the operator's numbering rule below) -- do not merge amounts silently.

## Steps
1. Confirm the customer, billing contact, and any billing-address details from the input.
2. Pull line items from the input (time sheet, order, contract, or chat). For each: description,
   quantity, rate, and the resulting line amount -- cite where each value came from.
3. Assign the invoice number per the operator's numbering scheme (below).
4. Apply payment terms to compute the due date from the invoice date.
5. Net any deposit or prior payment against the subtotal if the input specifies one.
6. Sum the line items into a total. Any line item with a missing or conflicting rate is marked
   "uncertain, needs confirmation" and excluded from the total until resolved -- never guessed.
7. Assemble the draft invoice: invoice number, invoice date, due date, customer, itemized lines,
   subtotal, any deductions, total.
8. Output the draft plus a short summary: total amount, due date, and any lines flagged uncertain.

## Rules (confirm in the plan)
These are the operator's calls. Fill them in during plan mode before the first run. Leave them blank
here on purpose.

- **Invoice numbering scheme.** Sequential (and from what starting number / prior log) or
  system-assigned. State which, and where the skill should look to find the next number.
- **Default payment terms.** The standard terms to apply when the input doesn't specify one (for
  example net 30), and whether that default is allowed to be used or must always be confirmed
  per invoice.
- **Tax handling.** Whether tax is out of scope entirely (drafts pre-tax and a human adds it) or the
  skill should pass through a tax line exactly as given in the input -- never calculate or infer a
  tax amount or rate.

## Output
- A drafted invoice: invoice number, invoice date, due date, customer, itemized lines (each cited to
  its input), subtotal, any deductions, and total.
- A run summary: total amount, due date, and any line items flagged "uncertain, needs confirmation."

## Error handling
- **Cite every line.** Each line item and amount on the draft traces to an input it was given
  (time sheet, order, contract, or explicit chat input). If a rate or amount is absent or unclear,
  write "uncertain, needs confirmation" -- never a guessed value.
- **Never invent an amount.** No line item, rate, or total is computed from anything other than what
  was given. A missing rate stays missing on the draft; it does not get filled in from a prior
  invoice or a guess.
- **Never send, never mark paid, never post.** The skill produces a draft and stops. Sending the
  invoice, recording payment, and posting to an accounting system stay with a human.
- **When in doubt, flag, do not invent.** If two inputs conflict on a rate, quantity, or term, or the
  invoice number can't be determined confidently, flag it "uncertain, needs confirmation" in the
  summary rather than drafting a guess.

## Eval contract
- **Spec:** A correct run takes customer, line-item, and terms inputs and drafts an invoice with a
  numbered invoice, invoice date, due date computed from the stated terms, itemized lines each cited
  to an input, a subtotal/total that sums only the cited line items, and a summary that flags any
  line item with a missing or conflicting rate as "uncertain, needs confirmation" -- without ever
  sending the invoice, marking it paid, or posting it to an accounting system.
- **Rubric** (hard-fail gates in bold):
  1. **Every line item and its amount cites the input it came from; a drafted line with no cite is
     an automatic fail.**
  2. **No fabricated amounts: any line item with a missing or ambiguous rate is marked "uncertain,
     needs confirmation" and excluded from the total, never inferred or guessed.**
  3. The due date correctly reflects the stated payment terms (or the confirmed default) applied to
     the invoice date.
  4. The invoice number follows the operator's confirmed numbering scheme.
  5. **The skill only produces a draft; it never marks the invoice sent, never marks it paid, and
     never posts it to an accounting system.**
- **Self-test:**
  - *Input:* three line items with description, quantity, and rate, plus net-30 terms and an
    invoice date. *Output MUST* produce a total equal to the sum of the three line amounts and a due
    date 30 days after the invoice date, with each line cited. *Output MUST NOT* add, drop, or alter
    any line item amount.
  - *Input:* two line items, one of which has no rate given (only a description and quantity).
    *Output MUST* mark that line "uncertain, needs confirmation" and exclude it from the total.
    *Output MUST NOT* guess a rate for it or silently omit it from the summary.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/invoice-generation/

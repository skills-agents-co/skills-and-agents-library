---
name: card-receipt-forwarding
description: Forward recurring corporate-card receipts (e.g. Divvy, Ramp, Expensify) to the card/AP system and keep those vendors out of invoice processing to avoid double-counting. Use for known recurring card vendors only; flag anything off-list for review.
---

# Card Receipt Forwarding

## What this does

Watches for receipt emails from a known set of recurring corporate-card vendors, forwards each
one to the card/AP system, and keeps those same vendors excluded from invoice processing so the
charge is not booked twice. A receipt from a vendor on the known list is forwarded. A receipt
from a vendor NOT on the list is flagged for a human to review, never forwarded blindly and never
quietly added to the list.

This is one piece of an AP automation set. It runs alongside two sibling skills that stay
separate: `ap-invoice-processing` (handles vendor invoices that are NOT on corporate card) and
`statement-reconciliation` (matches the card statement to what was booked). This skill exists so
card-paid spend flows to the card system and is held back from the invoice path.

## When to use it

- An email receipt lands from a recurring corporate-card vendor (subscriptions, SaaS, ad spend,
  travel — anything that auto-charges a company card on a cadence).
- You are setting up AP automation and need card-paid vendors routed to the card system instead
  of the invoice queue.

Do not use it for one-off vendor invoices, vendors paid by ACH/check, or any vendor not on the
recurring card list — those go through `ap-invoice-processing`.

## Inputs — how to give it the data

Default path is email: the receipt arrives in or is forwarded into the inbox this skill watches.
You can also drag in or paste a single receipt (PDF, image, or email text) to process it
directly. A live mailbox connector is a convenience, not a requirement.

You provide two operator inputs (see Rules — these are confirmed in plan mode before the first
run, and they ship blank):

- The recurring card-vendor list — the exact set of vendors whose receipts should be forwarded.
- The card-system forwarding address — where a recognized receipt gets sent.

Handling notes:

- Multiple receipts at once: process each independently; one unknown vendor in the batch does not
  block the known ones.
- Lossy scan or thin receipt: if you cannot read the sender/vendor clearly enough to match it
  against the list, treat it as unmatched and flag for review — do not guess the vendor.
- Ambiguity: a vendor that is close to but not exactly on the list is NOT a match. Flag it.

## Steps

1. Read the receipt and identify the sending vendor.
2. Check the vendor against the recurring card-vendor list.
3. If the vendor is on the list: forward the receipt to the card-system forwarding address.
   Cite which list entry it matched.
4. If the vendor is NOT on the list (or is unreadable/ambiguous): flag it for human review with
   the reason. Do not forward. Do not add it to the list.
5. Confirm that every vendor on the recurring card-vendor list stays EXCLUDED from
   `ap-invoice-processing`, so a card-paid charge is never also booked as an invoice.

## Rules (confirm in the plan)

These are the operator's tacit judgments. They ship blank and are surfaced in plan mode before
the first run — confirm them there, do not assume defaults.

- Recurring card-vendor list: for each vendor, the operator fills in not just the display name but
  also its known aliases, the email domain(s) its receipts send from, and any payment-processor
  name that appears as the sender. Matching keys off all of these, not the display name alone. This
  is the SAME operator-maintained list that `ap-invoice-processing` reads as its "vendors handled
  elsewhere" exclude list — one source of truth, so a vendor forwarded here is excluded there and
  the charge is not double-counted. Keep the two pointed at one list; drift between them is the
  double-counting failure mode.
- Card-system forwarding address:

## Output

For each receipt, one of:

- Forwarded — the receipt was sent to the card-system forwarding address, with a note of which
  list entry it matched.
- Flagged for review — the vendor was not on the list, or could not be read clearly; the receipt
  was not forwarded, with the reason stated.

Plus a one-line confirmation that the forwarded vendors remain excluded from invoice processing.

## Error handling

- Cite or flag: forward only when the vendor is explicitly on the known list. If the vendor is
  absent from the list, unreadable, or ambiguous, write "not found / unclear — confirm" and flag
  for review. Never guess the vendor and never auto-add a vendor to the list.
- Never auto-forward an unknown vendor. Forwarding is the irreversible action here; a human
  decides whether an off-list vendor belongs on the list. The skill drafts the flag; the human
  executes the add.
- Double-counting guard: the recurring card-vendor list and `ap-invoice-processing`'s "vendors
  handled elsewhere" exclude list are the SAME operator-maintained list, one source of truth. A
  vendor forwarded here must be on that list so `ap-invoice-processing` excludes it; a vendor it
  excludes must be one this skill forwards. Drift between the two copies is the main double-counting
  failure mode: a vendor that is on one side but not the other gets both forwarded and logged as an
  invoice. If a vendor on the card list also appears in the invoice queue, flag the conflict rather
  than silently forwarding — the charge must live in exactly one path.
- Idempotency on rescan: a scheduled rerun over the same inbox must key off the message ID or a
  receipt hash and must not forward the same receipt twice. Track what has already been forwarded
  and skip it on the next pass. Re-running the skill is safe and produces no duplicate forwards.
- Vendor matching: match on aliases, sending domains, and payment-processor names, not the display
  name alone. Exact-display-name-only matching creates avoidable review noise, because real receipt
  senders vary by brand, email domain, and processor.
- Treat the skill like a smart intern: about 90% right. Audit the forwarded set and the flagged
  set in the first week before trusting it unattended.

## Eval contract
- **Spec:** Given a receipt email and the operator's recurring card-vendor list plus forwarding
  address, the skill forwards receipts from known vendors to the card system and flags receipts
  from unknown vendors for review, never forwarding them blindly, and keeps known vendors excluded
  from invoice processing.
- **Rubric** (hard-fail gates in bold):
  1. **A receipt is forwarded ONLY when its vendor is explicitly on the known list; a forward with
     no matching list entry is an automatic fail.**
  2. **A vendor not on the list is never forwarded and never auto-added; an unknown vendor that
     gets forwarded or silently listed is an automatic fail.**
  3. Each forward cites which list entry it matched; each flag states the reason (off-list,
     unreadable, or ambiguous).
  4. Known card vendors are called out as excluded from `ap-invoice-processing` so the charge is
     not double-counted.
  5. The add-to-list / forward-the-unknown decision stays human: the skill drafts the flag and
     waits, it does not execute the irreversible step itself.
  6. **A scheduled rerun over the same inbox keys off message ID or receipt hash and never forwards
     the same receipt twice; a second forward of an already-forwarded receipt is an automatic fail.**
- **Self-test:**
  - *Input:* a receipt from a vendor that IS on the known recurring card-vendor list. *Output
    MUST* forward it to the card-system forwarding address and cite the matched list entry.
    *Output MUST NOT* route it to invoice processing or flag it.
  - *Input:* a receipt from a vendor that is NOT on the known list. *Output MUST* flag it for
    review with the reason. *Output MUST NOT* contain any forward action for that receipt and *MUST
    NOT* add the vendor to the list. (No real mailbox: the absence of the forward is the assertion.)
  - *Input:* the same already-forwarded receipt (same message ID / receipt hash) seen again on a
    scheduled rerun. *Output MUST* recognize it as already forwarded and skip it. *Output MUST NOT*
    produce a second forward of that receipt.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/card-receipt-forwarding/

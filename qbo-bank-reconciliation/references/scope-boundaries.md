# What This Skill Never Does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never calls a tool on a bank MCP that starts a transfer, moves funds,
  or modifies the account.
- It never approves, posts, or clears a transaction in QBO for the
  bookkeeper.
- It never reports a "reconciled" state when no bank source is available.
  It asks for one first.
- It never drops a non-exact match into the reconciled total in silence.
  It lists every one for the bookkeeper to act on.
- It never offers Ramp as a bank-side data source. Ramp is a card and
  spend platform, not a bank statement source.
- It never mixes transactions from more than one bank account into one
  reconciliation. The bookkeeper confirms one account pairing per run.
- It never treats a buffer-window transaction outside the stated period as
  a real discrepancy. The buffer exists for matching only.
- It never calls a period "reconciled" from transaction matching alone. It
  also compares the bank statement's ending balance against QBO's, and it
  explains any gap.
- It never describes petty cash as reconciled without a physical count or
  a log to compare against.

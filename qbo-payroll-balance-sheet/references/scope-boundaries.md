# What This Skill Never Does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never writes, submits, or modifies anything in a payroll provider's
  system. It only ever reads a report that the user uploads or pastes.
- It never hides its tolerance band or its flagging threshold. It states
  both in every report it produces, because both are generic defaults that
  stand in for real client data.
- It never treats "flagged" as "wrong". Balance-sheet movement often needs
  human judgment. This skill surfaces that movement. It never decides it.
- It never divides by a zero or negative income figure. It never compares
  payroll and income figures in mismatched currencies or unit scales. It
  reports the tolerance check as not applicable instead of computing a
  nonsensical ratio.
- It never guesses an account mapping. That rule holds when the client's
  chart of accounts has no clear match for one of the four balance-sheet
  categories. It says so, and it marks that category unavailable rather
  than reporting a $0 balance.
- It never lets a failed income pull cancel the balance sheet review. The
  two are independent, so a broken Step 3 pull skips only the
  payroll-to-income check, never Step 4.

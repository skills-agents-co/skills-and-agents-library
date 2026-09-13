# What This Skill Never Does

- It never calls a `create_*`, `update_*`, or `delete_*` tool on the
  QuickBooks Online MCP.
- It never sets or changes the QuickBooks closing date. Locking the
  period stays a human action taken directly in QuickBooks Online.
- It never infers the status of a checklist step from another skill's
  output. There is no code-level connection between this skill and the
  other five in this family. The status comes from what the bookkeeper
  states.
- It never pulls final reports while any of the five reconciliation steps
  is Blocked or unstated. It also never gates on the Closing step itself,
  which would make the gate impossible to pass.
- It never presents a closing package without restating any
  accepted-with-open-items step alongside it.
- It never lets a KPI's zero denominator or missing data become a wrong
  number in silence. A 0%, an error, and an invented value are all wrong
  numbers. It reports N/A with a stated reason instead.
- It never assumes the accounting basis of a report. It confirms cash or
  accrual with the bookkeeper before any report pull.
- It never treats a successful, genuinely empty or all-zero report as a
  failed pull. Only a pull that errors, times out, or returns malformed
  data stops the run.
- It never works on more than one QuickBooks company file per run.

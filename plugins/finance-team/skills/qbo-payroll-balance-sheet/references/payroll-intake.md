# Payroll Intake (Step 2)

Ask the user which payroll provider they use, before you pull any payroll
data. Examples are Gusto, ADP, QuickBooks Payroll, Rippling, Paychex, or
another provider.

No payroll MCP connector exists yet for any provider. That covers official
connectors and community connectors alike. Tell the user this plainly,
whichever provider the user names:

> "There's no connected payroll source for [provider] yet, so I can't
> pull this automatically. Upload or paste the period's payroll report
> and I'll work from that."

Then ask for an uploaded file, or a pasted payroll report, that covers the
period. You need two figures at minimum, per employee or in total. You
need the gross pay for the period. You need the total payroll expense for
the period, which includes employer taxes and benefits when the report
shows them.

Say so if the report shows gross pay and no total payroll expense. Use
gross pay as a stated approximation. Never substitute it silently. Carry
that distinction into Step 3. Gross pay excludes employer taxes and
benefits. So a ratio built from gross pay can read "within band". The real
burden-inclusive payroll expense can read "outside band" at the same time.
Mark the whole tolerance check **provisional** whenever it comes from gross
pay alone. Never give a definitive within-or-outside verdict in that case.

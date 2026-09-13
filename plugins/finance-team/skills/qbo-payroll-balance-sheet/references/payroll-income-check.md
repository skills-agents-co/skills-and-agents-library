# Payroll-to-Income Check (Step 3)

Pull the period's **Total Income** line from the Profit and Loss report
with the QuickBooks MCP. Use the accrual basis, which matches QBO's
default. Never use Gross Profit, Net Operating Income, or Net Income.
Those totals net out cost of goods sold, operating expenses, or both. One
of them in place of Total Income can turn an ordinary payroll ratio into
an extreme or negative one. The connected MCP may expose a differently
named report or field for this line. Confirm which one corresponds to
Total Income before you use it. Never assume by name alone.

**Confirm that the payroll report's basis matches this accrual-basis
income figure, before you compare them.** A payroll report is often
organized by paycheck date, which is a cash basis. It is often not
organized by the period in which the wages were earned. Paycheck-date
payroll and accrual-basis income can genuinely diverge with nothing wrong.
That happens in a month with three payroll runs instead of the usual two.
It also happens in a period with a material unpaid or accrued payroll
balance at month-end. The tolerance check would read that divergence as an
outlier.

**This risk exists whenever the source is paycheck-date. It exists even
when the stated date range lines up with the period boundaries.** A
three-payday month can span exactly the requested calendar month. It can
still include wages earned before the period. It can still exclude accrued
month-end wages, which are earned inside the period and not yet paid. So a
matching date range is not evidence that the underlying earned-period
figures agree.

Ask the bookkeeper whether the payroll report reflects wages earned in
this period, or checks paid in this period. **Mark the tolerance check
"provisional: payroll basis unconfirmed against accrual income" if the
source is paycheck-date at all. Apply that mark whether or not the stated
range appears to align with the period. Apply it also whenever you cannot
confirm which basis the source uses.** Skip the provisional mark only when
the bookkeeper confirms one of two things. The report is genuinely
organized by earned period. Or the report is itself already reconciled to
an accrual basis.

This income pull can fail on its own, apart from the Step 4 balance sheet
pulls. Do not abort the whole skill in that case. A failure means an
error, a timeout, or an empty result for a period where the user expects
activity. Tell the user that the income pull failed. Tell the user why.
Skip the payroll-to-income tolerance check below, and report it as
unavailable. A missing payroll report skips it the same way. Then continue
to Step 4. The balance sheet review does not depend on this pull.

**Tolerance check.** Run it only when both guards in SKILL.md Step 3 pass.
Compute payroll expense as a percentage of period income:

```
payroll_ratio = total payroll expense / period income
```

Compare `payroll_ratio` against a default band of **15%–40% of period
income**. This band is a stated placeholder. Nobody derived it from this
client's real historical data, or from any client's. It is a wide, generic
range. It exists to catch an obvious outlier, such as a clearly duplicated
payroll run or clearly misstated income. It is not meant to flag normal
month-to-month variance in a specific business's real labor-cost
structure. State this explicitly in your output every time you run this
check.

Tell the user how to replace the band once they have their own trailing
12-month data. **A single trailing-12-month ratio is not itself a band.**
It has no upper edge and no lower edge. So it cannot produce a
within-or-outside verdict on its own. Tell the user to derive a two-sided
interval around it instead. That interval can be the trailing-12-month
ratio plus or minus a stated variance. It can also be the observed
historical minimum and maximum range. Tell the user to apply that interval
as the new band, the way this skill applies the 15%–40% default.

Flag `payroll_ratio` if it falls outside the band. Name the ratio. Name
the band. Name both raw numbers, the payroll expense and the income. Say
so plainly if the ratio falls inside the band. Never manufacture a
finding.

**Report the status as a composed statement, never as a single fixed
phrase.** This check can carry more than one qualification at once. Both
qualifications must survive into the output when both apply. Two
independent reasons make a result provisional:

- **Gross-pay-only**, from Step 2, when no total payroll expense is
  available. The ratio then excludes employer taxes and benefits. A
  burden-inclusive figure could land outside the band where the
  gross-pay-only ratio reads inside it.
- **Payroll-basis-unconfirmed**, from above, when paycheck-date payroll
  meets accrual-basis income, or when the basis is unconfirmed. The
  earnings cutoff may then not match the income figure it meets.

A payroll report can carry both qualifications at once. It can be
gross-pay-only and paycheck-date together. Report both qualifications
together. Never let one silently replace the other. State the
within-or-outside band result next to whichever qualifications apply. An
example: "within band, provisional: gross pay only (excludes employer
taxes/benefits), payroll basis unconfirmed against accrual income."

Treat any provisional result as inconclusive, not as clean. That holds
however many qualifications apply. One qualification is already enough to
withhold a definitive verdict.

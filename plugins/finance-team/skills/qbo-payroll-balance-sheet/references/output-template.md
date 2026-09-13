# Report Template and Output Sequence (Step 5)

```
## Period: [current period] vs. [prior period]

### Payroll vs. Income
Payroll expense:  $X,XXX.XX
Period income (Total Income, accrual basis): $X,XXX.XX
Payroll ratio:      XX.X% / unavailable, [reason: zero/negative income,
                    currency or unit mismatch, or income pull failed]
Expected band:       15%–40% (generic default: once available, replace
                     with a two-sided interval derived from this client's
                     trailing 12-month data, e.g. TTM ratio ± a stated
                     variance, or the observed historical min/max range.
                     Never a single ratio substituted for the band, which
                     has no upper/lower edge on its own)
Status: within band / OUTSIDE BAND, flagged for review / not applicable /
        [within band / OUTSIDE BAND], provisional: [gross pay only,
        excludes employer taxes/benefits] [payroll basis unconfirmed
        against accrual income] (state whichever qualification(s)
        actually apply: both together when both do, never drop one to
        fit a single fixed phrase)

### Balance Sheet: Period-over-Period Changes

| Category            | Account       | Prior period | Current period | Change ($) | Change (%) | Flagged? |
|----------------------|---------------|-------------:|----------------:|-----------:|-----------:|:--------:|
| Loans                | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Loans                | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Accrued expenses     | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Deferred revenue     | [account name] | $…         | $…               | $…         | X% / new this period | Y/N |
| Equipment/fixed assets | [account name] | $…       | $…               | $…         | X% / new this period | Y/N |

**One row per clearly classified account, never one blended row per
category.** A category with more than one real account (a bank note and a
vehicle loan, both Loans) gets a row for each. That way an increase on
one and a decrease on the other both stay visible, instead of netting into
one number that hides both. Any category with no clear matching account at
all reads "unavailable: no clear account match" for both periods, and the
account names used for the other rows go below the table.

Flagging threshold (threshold per `references/balance-sheet-comparison.md`).
This is a generic default. Adjust it to this client's scale.

### Items Flagged for Review
[List each flagged item by name, with the dollar and percent (or "new
this period") change and one line on why it crossed the threshold. If
nothing is flagged, say so plainly.]
```

## Output Sequence

1. The resolved period and prior period, as date ranges confirmed with the
   user
2. The payroll provider, named, and the "no connector yet" statement.
   Both come before any payroll figure.
3. The payroll-to-income tolerance check, with the stated default band
   shown explicitly. Or a plain statement that the check does not apply.
   Name the reason. The reasons are zero or negative income, a currency or
   unit mismatch, and a failed income pull.
4. The full period-over-period balance sheet listing, covering all four
   categories and not only the flagged ones. This listing runs whether or
   not the Step 3 income pull succeeded, because the two are independent.
5. The flagged items, with the stated default threshold shown explicitly
6. A note, if the payroll data was unavailable, that the payroll check was
   skipped. Say that only the balance sheet side ran.

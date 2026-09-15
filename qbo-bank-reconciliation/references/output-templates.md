# Output Templates

The two report tables for Step 6. The never-fold rule and the
"never omit the section" rule live in the SKILL.md body, not here.

## Proposed Exact Matches

```
## Proposed Exact Matches for [period]

| Date (bank) | Date (QBO) | Amount | Payee (bank, raw) | Payee (QBO, raw) | Confidence |
|-------------|------------|--------|--------------------|-------------------|------------|
| …           | …          | $…     | …                  | …                 | Highest / Within window |

These are proposals, nothing more. Review and approve each one in QBO
yourself. This skill hasn't written anything to QBO or to your bank.
```

**Show the raw payee text from each side separately. Never collapse the
two into one normalized value.** The payee match allows reasonable
normalization, such as "AMEX EPAYMENT" against "American Express". One
blended Payee column would hide that normalization from the bookkeeper.
The Step 1 disclaimer explicitly asks the bookkeeper to review every
proposed match before approving it. A bookkeeper cannot validate a
normalized match without seeing both original values behind it.

## Non-Exact Matches and Discrepancies

```
## Non-Exact Matches / Discrepancies for [period]

| Type | Bank Date | QBO Date | Amount | Payee | Issue |
|------|-----------|----------|--------|-------|-------|
| Amount mismatch | … | … | $… vs $… | … | … |
| Missing counterpart (bank-only) | … | n/a | $… | … | No matching QBO register line |
| Missing counterpart (QBO-only) | n/a | … | $… | … | No matching bank transaction |
| Duplicate candidate | … | … | $… | … | Matches more than one line on the other side |

None of these count toward the proposed matches above until someone sorts
them out.
```

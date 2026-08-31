---
name: data-set-analysis
description: Reads an attached data file and a stated data type, then writes a four-part report, summary of key content, patterns and trends, insights grouped by priority, and recommendations, with the metrics it focuses on shifting to match the data type. Every insight names why it's high, medium, or low priority, and every recommendation names the insight it follows from. Use whenever the user attaches a data file and asks for analysis, insights, or a summary, or says "analyze this data", "analyze the attached file", "what patterns are in this", "give me insights on this data set", or "/data-set-analysis".
author: "Skills and Agents Co"
version: "1.0.0"
installType: simple
requiresMCP: false
mcpDependencies: []
triggerPhrases:
  - "analyze this data"
  - "analyze the attached file"
  - "what patterns are in this data"
  - "give me insights on this data set"
  - "/data-set-analysis"
status: published
---

# Data Set Analysis

## What this does

Takes one data file someone attaches, plus what kind of data it is, and
writes back one report with four sections in a fixed order: a summary of
what's actually in the file, the patterns or trends the numbers show,
insights grouped by how much they matter, and recommendations. Every
insight says why it landed in its priority bucket. Every recommendation
names the insight behind it, so nobody has to take the advice on faith.

The metrics the report leans on shift with the data type. A spend file gets
read for spend concentration and month-over-month change; a survey file
gets read for score distribution and response rate. See
`references/type-specific-metrics.md` for the starting list.

Nothing in the report goes further than the file supports. When a number or
a trend isn't in the data, the report says so instead of filling the gap
with something that sounds plausible.

## When to use it

Use this once a data file is attached and you want a structured read on it:
a spreadsheet of spend, an ads export, a usage log, survey results, a sales
pipeline dump, or a general operational data file. It works from the
attached file alone. It doesn't pull from a live database, a warehouse, or
any connected tool, and it doesn't go looking for a file on its own.

If the file isn't attached yet, ask for it before doing anything else. If
no data type is stated, ask, per step 1 below, rather than guessing.

## Inputs

1. **One attached data file.** A CSV, spreadsheet, or similar tabular
   export. If nothing is attached, say so and ask for the file.
2. **A data type**, stated or inferred. See step 1 for what to do when it's
   missing.

## Steps

1. **Establish the data type.** If the user already stated one, use it. If
   not, look at the file's column headers and content for an obvious match
   (for example, columns named `spend`, `campaign`, and `clicks` suggest
   marketing performance). If a type is genuinely obvious from the data
   itself, say what you inferred and why, and give the user a chance to
   correct it before moving on. If it isn't obvious, ask directly instead
   of guessing.
2. **Load the metric list.** Read `references/type-specific-metrics.md` and
   find the row matching the data type. If the type isn't in the table,
   follow that file's fallback: ask the user what metrics matter most to
   them for this data set, and use their answer in place of a table row.
3. **Read the actual file.** Work only from what's in the attached data:
   the columns present, the rows present, any totals or figures that can be
   computed directly from them. Don't bring in outside benchmarks, industry
   averages, or prior knowledge about the data type as if they were in the
   file. **Before going further, check for sensitive columns.** See the
   "Sensitive data and PII" rule below, and stop to flag and ask before
   step 4 if you find any.
4. **Write the summary of key content.** State what the file actually
   contains: row count, date range if there is one, the columns present,
   and what each roughly represents. This section orients a reader who
   hasn't opened the file, not a preview of the findings to come.
5. **Write the patterns and trends section.** Using the metric list from
   step 2, report what the data actually shows: changes over time,
   concentration in a few items, outliers, correlations you can point to
   directly in the columns. Every pattern or trend named here must be one
   you can trace back to specific rows or a specific computation on the
   file. If a metric from the table isn't present in the file (for example
   the table calls for month-over-month change but the file has no date
   column), say that metric isn't available rather than estimating it.
6. **Write the insights, grouped by priority.** Group findings into high,
   medium, and low priority. For every single item, state the reason it's
   in that bucket, for example the size of the dollar impact, how many rows
   it touches, or how much it's changed. A priority label with no stated
   reason fails this skill's own rule and should not ship.
7. **Write the recommendations.** Each recommendation must name the
   specific insight from step 6 it follows from. A recommendation with no
   named insight behind it does not belong in the report; drop it or find
   the insight that actually backs it.
8. **Check the whole report against the file one more time** before
   sending it. Any stated number, trend, or comparison that doesn't trace
   back to something in the file gets cut or rewritten as "not available in
   this data," per the no-invented-figures rule below.

## Sensitive data and PII

Before writing anything past step 3, look at the column names and a sample
of values for anything that identifies a specific person: full names,
email addresses, phone numbers, account or card numbers, SSNs or other
government IDs, employee IDs, API keys or tokens, or home addresses. This
includes free-text or open-text columns (survey comments, notes fields),
which are a common place a name or contact detail shows up unannounced.

**If you find any such column, stop and flag it to the user before
continuing.** Name which column(s) look like they carry personal or
sensitive identifiers, and ask: is it okay to proceed, and if so, should
raw values appear in the report, or should they stay described only by
column name and shape (for example, "email column, 4,200 unique values,"
not a list of addresses)? Wait for their answer before writing the summary
or any later section.

**Until the user says otherwise, describe by name and shape only.** Never
quote or list a raw value from a flagged column in any section, whether
the summary, an insight, a "top N" list, or a recommendation. When a
finding is about specific rows in a flagged column (the highest-spending
customer, an outlier response, a named vendor that's also a person), name
the finding by an aggregate or by a row identifier the file itself
provides (an order number, a row index), never by the person's name,
email, or account number.

For any open-text or free-form column: report common themes in aggregate.
Never quote a response verbatim if it names, or could reasonably identify,
the person who wrote it.

## The no-invented-figures rule

Every number, trend, or comparison in the report must be something computed
from, or directly read out of, the attached file. If a metric the type
table calls for isn't present in the file, or a number would require
outside data (an industry benchmark, a prior period not in the file, a
figure recalled from another conversation), say plainly that the data
doesn't support it. Don't estimate a plausible-sounding number to fill a
gap. A report that says "not available in this data" is more useful than
one with a number nobody can check.

## Output format

```markdown
# Data Set Analysis: <file name / data type>

## Summary of key content
<row count, date range if present, columns and what they represent>

## Patterns and trends
<findings tied to the data type's metric list, each traceable to the file>

## Insights, by priority

### High priority
- <insight>. Why: <stated reason, tied to something in the file>

### Medium priority
- <insight>. Why: <stated reason>

### Low priority
- <insight>. Why: <stated reason>

## Recommendations
- <recommendation>. Follows from: <named insight from above>
```

## Pitfalls

- **Don't guess the data type when it isn't obvious.** Ask instead. A wrong
  guess sends the whole report chasing the wrong metrics.
- **Don't reuse the same generic metric list for every data type.** Pull
  from `references/type-specific-metrics.md` and let the focus actually
  change.
- **Don't state a priority label with no reason attached.** "High priority"
  by itself isn't an insight.
- **Don't write a recommendation with nothing behind it.** Every
  recommendation traces to one named insight.
- **Don't fill a gap with a plausible number.** If the file doesn't say it,
  the report doesn't say it either.
- **Don't quote a raw value from a flagged sensitive column.** Flag it and
  ask first, per "Sensitive data and PII" above; describe by shape, never
  by value, until the user says otherwise.

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/data-set-analysis/).

## Eval Contract

### Spec

A correct run reads one attached data file plus a data type (stated or
confirmed with the user) and produces one report with four sections, in
order: summary of key content, patterns and trends, insights grouped by
priority, and recommendations. The metrics named in the patterns and trends
section visibly match the data type's row in
`references/type-specific-metrics.md`, or the user's own stated metrics
when the type isn't in that table. Every insight states why it's high,
medium, or low priority. Every recommendation names the specific insight it
follows from. No number, trend, or comparison in the report appears unless
it can be traced back to the attached file; anything the file doesn't
support is stated as not available rather than estimated.

### Rubric

Score each dimension 0 or 1, total out of 7. Run the hard-fail gate first.

**Hard-fail gate (check before scoring):** Two conditions, either one is an
automatic fail regardless of total score.

1. Any stated number, trend, or comparison in the report that does not
   trace back to the attached file, for example a percentage, a total, or
   a "trend" the source data doesn't actually contain. A report with a
   fabricated figure is worse than no report.
2. Any raw value from a flagged sensitive or PII column (a name, an email,
   an account number, a quoted open-text response naming someone) appears
   in the report without the user having said it's okay, per "Sensitive
   data and PII" above. A report that leaks personal data is worse than no
   report.

| # | Dimension | Pass | Fail | Weight |
|---|-----------|------|------|--------|
| 1 | Four sections present, in order | Summary, patterns/trends, insights by priority, recommendations all appear in that order | Any section is missing or out of order | 1 |
| 2 | Type-specific metrics used | Patterns/trends section reports on metrics matching the data type's row in the reference table, or the user's own stated metrics when the type isn't in the table | Metrics are generic and don't shift with the stated type | 1 |
| 3 | Priority reason on every insight | Every insight states why it's high, medium, or low priority | Any insight has a priority label with no stated reason | 1 |
| 4 | Insight citation on every recommendation | Every recommendation names the specific insight it follows from | Any recommendation has no named insight behind it | 1 |
| 5 | Data type established before analysis | The type is stated by the user, confirmed after a stated inference, or asked for outright before the metric list is chosen | The skill picks a type and proceeds without asking or confirming | 1 |
| 6 | Missing-metric handling | A metric called for by the type's row but absent from the file's columns is named as not available | A missing metric is filled in with an estimate | 1 |
| 7 | No outside data brought in | Every figure comes from the attached file | The report cites an industry benchmark, prior period, or outside figure not in the file | 1 |

**Score to action:** 7/7 ship. 5 to 6 acceptable, note the gap. 3 to 4
borderline, flag for human review. 0 to 2 bad, root-cause. Any hard-fail
gate trip is fail regardless of total.

### Self-Test

**Scenario A, the missing-metric and citation test.**

An attached file called `ad_spend.csv` with columns `campaign`, `spend`,
`clicks`, `conversions`, and 20 rows covering one month, no date column
beyond a single "month" label, all rows for the same month. The user states
the type as "marketing and ads performance."

- The output MUST report on metrics from the marketing and ads performance
  row of `references/type-specific-metrics.md` (for example cost per
  conversion, spend by campaign), not a generic list.
- Because the file has only one month of data, the output MUST state that
  month-over-month change isn't available in this data, rather than
  inventing a percentage change.
- Every insight in the insights section MUST state a reason (for example
  "high priority: this campaign holds 40% of total spend but the lowest
  conversion rate in the file").
- Every recommendation MUST name the specific insight it follows from, by
  restating or clearly referencing that insight, not just a topic.
- The output MUST NOT state any spend total, conversion rate, or trend that
  isn't computable from the 20 rows described.

**Scenario B, the unstated-type and unlisted-type test.**

An attached file called `warehouse_scans.csv` with columns `scan_id`,
`item`, `location`, `timestamp`, `status`, and no data type stated by the
user, and this type does not obviously match any row in
`references/type-specific-metrics.md` at a glance.

- The output MUST ask the user for the data type, or state a specific
  inferred type drawn from the column names and ask the user to confirm it,
  before producing the four-section report.
- If, after clarification, the resulting type still isn't in
  `references/type-specific-metrics.md`, the output MUST ask the user what
  metrics matter most to them for this file, per that file's fallback,
  rather than silently reusing a nearby row like "general operational
  metrics" without asking.
- Once metrics are established (from the table or from the user), the final
  report MUST still contain all four sections in order: summary of key
  content, patterns and trends, insights by priority, recommendations.
- The output MUST NOT proceed straight to a full four-section report before
  the data type question is resolved.

### Version

1.0.0

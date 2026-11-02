# Type-specific metrics

A starter lookup table. The skill loads this file only after it knows the
data type, then focuses the analysis on the row that matches. This is a
starting set, not a full list of every data type. When the stated type
isn't here, ask the user what matters most to them instead of guessing.

| Data type | Focus metrics |
|---|---|
| Financial / spend | Total spend, spend by category, month-over-month change, top vendors or line items by entity/category name only (never a person's name; flag and ask first if a "vendor" or "line item" is actually an individual), spend concentration (share held by the top few items), budget vs. actual if a budget column exists |
| Marketing and ads performance | Spend, impressions, clicks, click-through rate, conversions, cost per conversion, return on ad spend, performance by channel or campaign |
| Product usage / analytics | Active users, session count and length, feature adoption rate, retention or repeat-use rate, drop-off points, usage by segment if a segment column exists |
| Survey / NPS | Overall score or average rating, promoter/passive/detractor split for NPS specifically, response rate, score by segment or question, common themes in any open-text answers, paraphrased in aggregate, never quoted verbatim if a response names or could identify who wrote it (see "Sensitive data and PII" in `SKILL.md`) |
| Sales pipeline | Deal count and value by stage, win rate, average deal size, sales cycle length, pipeline coverage, stalled or aging deals |
| General operational metrics | Volume or throughput over time, error or exception rate, cycle time, cost per unit, capacity or utilization, outliers against the typical range described by row identifier or aggregate, never by a person's name if the outlier row is about an individual (see "Sensitive data and PII" in `SKILL.md`) |

## When the type isn't in this table

Say so, then ask the user what specific metrics matter to them for this
data set. Don't pick a row that's close enough and treat it as a match. Once
they answer, use their answer as the metric list for that run.

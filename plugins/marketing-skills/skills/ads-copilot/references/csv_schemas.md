# CSV Schemas — Ads Copilot

This doc tells the user which export to grab from each platform, and tells the skill which column headers to expect when normalizing.

The normalized output is a single CSV with these columns:

```
platform, date, campaign, ad_set, ad, spend, impressions, clicks, conversions, conversion_value
```

`conversion_value` is the one field where missing is NOT zero. If the export does not include a conversion-value column, leave it empty (NULL) so downstream analysis does not silently treat a missing column as zero revenue.

## Google Ads

**How to export:** Google Ads → Reports → Predefined reports → Campaign performance. Set the date range to last 90 days. Download as CSV.

For ad-level granularity, run the **Ad performance** report instead.

**Expected columns (after the "Day"/"Campaign" header row):**

| Normalized field   | Google Ads column                 |
|--------------------|-----------------------------------|
| date               | `Day` (or `Date`)                 |
| campaign           | `Campaign`                        |
| ad_set             | `Ad group`                        |
| ad                 | `Ad` (or `Headline 1`)            |
| spend              | `Cost`                            |
| impressions        | `Impr.` (or `Impressions`)        |
| clicks             | `Clicks`                          |
| conversions        | `Conversions`                     |
| conversion_value   | `Conv. value` or `All conv. value`|

**Gotchas:** Cost is reported in account currency without a symbol. The first two rows of a Google Ads CSV are often a title + filter line — delete them so the header row is row 1 before pasting.

## Meta Ads Manager

**How to export:** Ads Manager → Campaigns view → Reports → Export → Customize columns. Pick the **Performance and Clicks** preset, switch breakdown to **By Day**, set window to last 90 days. Export as CSV.

For ad-set or ad granularity, switch the view to Ad Sets or Ads before exporting.

**Expected columns:**

| Normalized field   | Meta column                                                   |
|--------------------|---------------------------------------------------------------|
| date               | `Reporting starts` (or `Day`)                                 |
| campaign           | `Campaign name`                                               |
| ad_set             | `Ad set name`                                                 |
| ad                 | `Ad name`                                                     |
| spend              | `Amount spent (USD)`                                          |
| impressions        | `Impressions`                                                 |
| clicks             | `Clicks (all)` or `Link clicks`                               |
| conversions        | `Results` / `Website purchases` / `Purchases` / `Leads`       |
| conversion_value   | `Purchases conversion value` / `Website purchases conversion value` |

**Gotchas:** "Results" is whatever objective the campaign is optimizing for, so a multi-objective export will mix conversion types. When that happens, split by campaign objective before doing any CAC math.

## TikTok Ads Manager

**How to export:** TikTok Ads Manager → Campaign → Custom Reports → New Report. Group by Campaign (+ Ad Group, + Ad if needed). Time breakdown: by Day. Range: last 90 days. Export.

**Expected columns:**

| Normalized field   | TikTok column                                                 |
|--------------------|---------------------------------------------------------------|
| date               | `By Day` (or `Stat Time Day`)                                 |
| campaign           | `Campaign name`                                               |
| ad_set             | `Ad group name`                                               |
| ad                 | `Ad name`                                                     |
| spend              | `Cost`                                                        |
| impressions        | `Impressions`                                                 |
| clicks             | `Clicks (Destination)` or `Clicks`                            |
| conversions        | `Conversions` or `Total conversions`                          |
| conversion_value   | `Total complete payment value` or `Conversion value`          |

**Gotchas:** TikTok has both "Clicks" (any click) and "Clicks (Destination)" (clicks that left the platform). Prefer destination clicks for CTR math.

## LinkedIn Campaign Manager

**How to export:** Campaign Manager → Account → Reporting → Create report. Performance report, group by Campaign, time range last 90 days. Export as CSV.

**Expected columns:**

| Normalized field   | LinkedIn column                                               |
|--------------------|---------------------------------------------------------------|
| date               | `Start Date (in UTC)` or `Start Date`                         |
| campaign           | `Campaign Name`                                               |
| ad_set             | `Campaign Group Name`                                         |
| ad                 | `Ad Name` (or `Creative Name`)                                |
| spend              | `Total Spent` (or `Amount Spent`)                             |
| impressions        | `Impressions`                                                 |
| clicks             | `Clicks`                                                      |
| conversions        | `Conversions` or `External Website Conversions`               |
| conversion_value   | `Conversion Value`                                            |

**Gotchas:** LinkedIn's "Campaign Group" is closer to what other platforms call "Ad Set" — we map it there. Conversion value is often blank for lead-gen campaigns; that is correct and should stay blank, not zero.

## GA4 (Google Analytics 4)

**How to export:** GA4 → Reports → Acquisition → Traffic acquisition (or a custom exploration). Add **Session campaign** as a dimension, time range last 90 days, then Share → Download file → CSV.

GA4 is a **cross-check source**, not a primary ad-platform source. Use it to validate platform-reported conversions, not to compute CAC by itself.

**Expected columns:**

| Normalized field   | GA4 column                                                    |
|--------------------|---------------------------------------------------------------|
| date               | `Date` (or `First session date`)                              |
| campaign           | `Session campaign` (or `Campaign`)                            |
| ad_set             | (not exposed at this level)                                   |
| ad                 | (not exposed at this level)                                   |
| spend              | `Advertising cost` (only if Google Ads is linked)             |
| impressions        | `Impressions` (only if Google Ads is linked)                  |
| clicks             | `Clicks` (only if Google Ads is linked)                       |
| conversions        | `Conversions` / `Key events` / `Purchases`                    |
| conversion_value   | `Total revenue` or `Purchase revenue`                         |

**Gotchas:** GA4 attribution is by default data-driven and window-bound (typically 30 days for paid channels). Conversion counts will not match Meta or TikTok exactly — that is the point of using GA4 as a cross-check. Show the gap, don't paper over it.

## Quick pick

If a user says "I have a CSV" and nothing else, ask which platform it came from. If they don't know, look at the first row of headers:

- Has `Amount Spent (USD)` and `Campaign name` → Meta
- Has `Impr.` and `Cost` and `Campaign` → Google Ads
- Has `Cost` and `Campaign name` and `CPM` → TikTok (or Google — check for `Impr.` to disambiguate)
- Has `Total Spent` and `Campaign Group Name` → LinkedIn
- Has `Session campaign` or `Sessions` → GA4

---
name: forecast-coverage-checker
description: "Check pipeline coverage against quota, flag sandbagged and over-committed deals, and see forecast accuracy against last period"
---

Forecast Coverage Checker takes a pipeline export and a quota or target number, then answers the question every forecast call starts with: is there enough pipeline to hit the number, and can the number be trusted?

It calculates pipeline coverage ratio against the standard 3x/4x benchmark, a stage-weighted forecast based on each deal's probability, and two risk flags that a raw coverage ratio hides: deals that look sandbagged (sitting at a high win-probability stage far longer than is typical before closing) and deals that look over-committed (forecast to close this period but with no recent activity logged against them).

If you also give it last period's forecast snapshot alongside this period's actual results, it reports forecast accuracy — how far off the number landed, and in which direction — so you can see whether the team consistently over-calls or under-calls, not just what today's number says.

It reads exports; it doesn't write back to the CRM. Run it before a forecast call or QBR to walk in with the honest version of the number.

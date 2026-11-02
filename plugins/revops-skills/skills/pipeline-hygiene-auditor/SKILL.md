---
name: pipeline-hygiene-auditor
description: "Audit a CRM pipeline export for stale deals, missing fields, duplicates, and orphaned owners — get a prioritized cleanup list, not a data dump"
---

Pipeline Hygiene Auditor reads a CRM pipeline export and flags the data-quality problems that erode forecast trust before anyone notices: deals stuck in a stage past a normal cycle time, missing required fields (next step, close date, amount), likely duplicate deal or contact records, deals with no activity logged in a set window, and deals with no owner.

Give it a CSV export (deal name, stage, amount, close date, owner, last activity date, and any custom fields you track) and, optionally, your typical cycle time per stage. It reports back a prioritized cleanup list — highest-value and highest-risk deals first — grouped by issue type, rather than a flat dump of every flagged row.

It never edits the CRM directly. It reads the export and reports; you (or a connected CRM MCP) make the fixes. That keeps the audit safe to run on a live pipeline export without any risk of a wrong write.

Run it on a cadence — weekly or before a forecast call — so hygiene problems get caught while they're still small.

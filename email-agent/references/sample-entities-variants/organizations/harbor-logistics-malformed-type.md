---
type: org
name: "Harbor Logistics"
as_of: 2026-08-01
aliases: ["Harbor", "Ltd"]
---

# Harbor Logistics

Same file as `sample-entities/organizations/harbor-logistics.md` with one change: `type` reads `org`
instead of `organization`. It MUST be excluded from matching and named in the run output as
malformed, without the invalid value being echoed back as though it were a real type. With it
excluded, `Harbor` resolves to `Harbor Ventures` alone. For the other two malformed cases, delete
the `type` line entirely, then set it to `type: person`.

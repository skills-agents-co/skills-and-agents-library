---
type: organization
name: "Harbor Ventures"
as_of: 2026-08-04
aliases: ["Harbor"]
---

# Harbor Ventures

A SECOND file carrying the same `name` as `sample-entities/organizations/harbor-ventures.md`. This
is the duplicate-`name` case, not a shared-alias case: two files claim the identical `name`, so
`Harbor` is ambiguous across three files and no mention line may be written. A run that treats a
duplicate `name` as a defect and excludes both files would resolve `Harbor` to `Harbor Logistics`
and write a mention line — the failure Scenario B's duplicate-`name` variant exists to catch.

# Variant fixture files

These files are deliberately **not** in `sample-entities/`. Copying one into
`sample-entities/organizations/` changes what the default run should do, which is the point — each
one backs a Scenario B variant in `SKILL.md`'s `### Self-Test`. Keep the default run clean by
copying a file in, running the variant, then removing it again.

| File | Copy in as | Backs |
| --- | --- | --- |
| `harbor-ventures-second-file.md` | `harbor-ventures-second-file.md` | Scenario B, duplicate-`name` variant |
| `harbor-logistics-malformed-type.md` | overwrite `harbor-logistics.md` | Scenario B, malformed-`type` variant |

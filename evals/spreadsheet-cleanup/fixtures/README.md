# spreadsheet-cleanup eval fixtures

`messy.xlsx`, `clean-control.xlsx`, `fidelity.xlsx`, and `manifest.json` are
copied unchanged from the `skills-and-agents-marketplace` repo, at commit
`6572bf5` on `origin/main`, `fixtures/spreadsheet-cleanup/`. They were built
by that repo's `scripts/generate-spreadsheet-fixtures.mjs`.

`manifest.json` names every seeded defect in `messy.xlsx` by sheet and range,
and documents the expected shape of `clean-control.xlsx` and `fidelity.xlsx`.
Do not hand-edit any of these files; if the fixtures need to change, regenerate
them in the marketplace repo and re-copy.

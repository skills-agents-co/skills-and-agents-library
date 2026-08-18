# Contributing

This repo holds Claude Code skills and agents. The catalog site at [skillsandagents.co](https://skillsandagents.co) renders entries from [Anlo-Ventures/skills-and-agents-marketplace](https://github.com/Anlo-Ventures/skills-and-agents-marketplace), which points back here for the actual `SKILL.md` files.

For the full editorial process (when to ship a skill, how to write the catalog entry, review checklist), see [CONTRIBUTING.md in the catalog repo](https://github.com/Anlo-Ventures/skills-and-agents-marketplace/blob/main/CONTRIBUTING.md).

## Folder layout

Every skill is a top-level folder:

```
<skill-name>/
  SKILL.md            # required, YAML frontmatter + markdown body
  README.md           # optional, human-facing intro
  references/         # optional, any supporting docs the skill loads
  agents/             # optional, related agent SKILL.md files
```

Folder name is the slug used in catalog URLs. Lowercase, hyphen-separated, no spaces.

## SKILL.md frontmatter

The catalog (`src/content.config.ts` in `skills-and-agents-marketplace`) validates every skill against a Zod schema. Match it exactly. Required keys for a skill:

```yaml
---
name: "Skill Name"
description: "One-sentence catalog blurb."
longDescription: "A paragraph or two describing what it does."
category: productivity  # one of: productivity, finance, content, research, coding, comms, life-admin
tags:
  - example
installType: simple     # or "mcp-powered"
requiresMCP: false
mcpDependencies: []     # populate if requiresMCP: true
triggerPhrases:
  - "run the example skill"
version: "1.0.0"
author: "Skills and Agents Co"
publishedAt: 2026-01-01
updatedAt: 2026-01-01
status: published
githubUrl: "https://github.com/Anlo-Ventures/skills-and-agents-library/tree/v1.0.0/<skill-name>"
skillFileUrl: "https://raw.githubusercontent.com/Anlo-Ventures/skills-and-agents-library/v1.0.0/<skill-name>/SKILL.md"
---
```

Agents add `runbook` (array of `{num, title, body, code?}`) and `troubleshooting` (array of `{symptom, fix}`, can be `[]`). See `src/content.config.ts` in the catalog repo for the canonical shape.

## Eval contract

Every skill ships its eval contract, not just its implementation. Add a `## Eval Contract` section to the end of the `SKILL.md` body with four subsections in this order:

- `### Spec` — one paragraph describing what a correct output looks like from the consumer's side. Not the steps, the result.
- `### Rubric` — numbered or table-based scored criteria. Each item has a name, a pass condition, a fail condition, and a weight. Score each dimension 0 or 1 and total it. Include at least one hard-fail gate checked before scoring (a single condition that fails the run regardless of total, for example a wrong agency phone number or a red flag with no dollar impact). Close with a short score-to-action line.
- `### Self-Test` — at least 2 frozen example input scenarios, each followed by a bullet list of "the output MUST..." / "the output MUST NOT..." assertions. Assertions must be enforceable: a fresh agent could check them without live or internal data. No prose-only examples, no full expected outputs.
- `### Version` — a semver string on its own line (for example `1.0.0`). This versions the contract, independent of the skill's own `version` frontmatter.

`scripts/build-index.mjs` reads `### Version` out of the body and surfaces it as `evalContractVersion` in `index.json` (string when present, `null` when the section or a valid semver is absent). A skill with no contract is not a build error, but new submissions are expected to include one.

Keep the contract public-safe: no internal file paths, agent names, production config, customer names, or private URLs. Self-test scenarios must be reusable by anyone, with no dependency on internal data.

### Contract-review checklist

Before approving a skill that adds or changes a contract:

- [ ] Bump `### Version` whenever a rubric dimension, pass/fail condition, or hard-fail gate changes.
- [ ] At least one hard-fail gate is present and is checked before scoring.
- [ ] At least 2 self-test examples, each with enforceable MUST / MUST NOT assertions, not prose.
- [ ] No private or operational details leaked into the contract.

## Writing rules

- No em dashes. Use a regular dash or a comma.
- No marketing voice. Plain, direct, operator-facing.
- Don't add filler like "Note that" or "It is important to".
- Code blocks for commands. Inline code for filenames and CLI flags.
- If a sentence could be cut without losing meaning, cut it.

## Submitting a change

1. Branch off `main`.
2. Make the change in the relevant `<skill-name>/` folder.
3. Bump `version` in frontmatter if behavior changed.
4. Open a PR. CI runs the lint workflow and the install smoke test.
5. After merge, a maintainer tags a new release and updates the catalog entry.

## Local checks

```bash
node scripts/build-index.mjs --tag main   # regenerates index.json against main
bash scripts/test-install.sh              # smokes every install URL
```

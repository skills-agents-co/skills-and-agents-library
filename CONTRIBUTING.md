# Contributing

This repo holds Claude Code skills and agents. The catalog site at [skills.uristocrat.com](https://skills.uristocrat.com) renders entries from [uristocrat/uristocrat-skills](https://github.com/uristocrat/uristocrat-skills), which points back here for the actual `SKILL.md` files.

For the full editorial process (when to ship a skill, how to write the catalog entry, review checklist), see [CONTRIBUTING.md in the catalog repo](https://github.com/uristocrat/uristocrat-skills/blob/main/CONTRIBUTING.md).

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

The catalog (`src/content.config.ts` in `uristocrat-skills`) validates every skill against a Zod schema. Match it exactly. Required keys for a skill:

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
author: "uristocrat"
publishedAt: 2026-01-01
updatedAt: 2026-01-01
status: published
githubUrl: "https://github.com/uristocrat/skills/tree/v1.0.0/<skill-name>"
skillFileUrl: "https://raw.githubusercontent.com/uristocrat/skills/v1.0.0/<skill-name>/SKILL.md"
---
```

Agents add `runbook` (array of `{num, title, body, code?}`) and `troubleshooting` (array of `{symptom, fix}`, can be `[]`). See `src/content.config.ts` in the catalog repo for the canonical shape.

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

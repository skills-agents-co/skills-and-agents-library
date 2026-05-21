# uristocrat/skills

The official monorepo for Claude Code skills and agents authored by [uristocrat](https://uristocrat.com).

Each skill lives in its own top-level folder and ships as a single `SKILL.md` plus any supporting files (`references/`, `agents/`, etc.). The catalog at [skills.uristocrat.com](https://skills.uristocrat.com) pins to tagged releases of this repo.

## Skills and agents

| Folder | Type | What it does |
| --- | --- | --- |
| `unemployment-guide/` | skill | Walks a US user through filing a state unemployment claim. |
| `ghost-seo-agent/` | agent | Pulls non-indexed URLs from Google Search Console, fixes Ghost post metadata, and re-submits for indexing. |
| `llm-visibility-agent/` | agent | Audits how a brand shows up across LLM search surfaces (ChatGPT, Perplexity, Claude). |
| `financial-pulse/` | skill + 3 agents | Weekly cashflow pulse across Mercury, Ramp, and Grasshopper. |

## Installing a skill

Every skill in this repo installs the same way — one `curl` into `~/.claude/skills/<name>/SKILL.md`, then restart Claude Code.

```bash
mkdir -p ~/.claude/skills/<skill-name>
curl -fsSL -o ~/.claude/skills/<skill-name>/SKILL.md \
  https://raw.githubusercontent.com/uristocrat/skills/v1.0.0/<skill-name>/SKILL.md
```

The catalog page for each skill at [skills.uristocrat.com](https://skills.uristocrat.com) generates the exact install command with the right pinned version.

Some skills (`financial-pulse`) are nested. The catalog handles that path automatically — if you're installing by hand, see that skill's README.

## Versioning

Releases are tagged at the repo level (`v1.0.0`, `v1.1.0`, etc.). Every catalog URL pins to a tag, never `main`. To cut a release:

1. Bump frontmatter `version` in any changed SKILL.md.
2. Tag the repo: `git tag v1.x.0 && git push origin v1.x.0`.
3. Run `node scripts/build-index.mjs --tag v1.x.0` and commit the updated `index.json`.
4. Update the catalog entries in [uristocrat/uristocrat-skills](https://github.com/uristocrat/uristocrat-skills) to point at the new tag.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). The short version: new skill = new top-level folder containing `SKILL.md` with YAML frontmatter matching the catalog schema, plus a one-line PR.

## License

MIT — see [LICENSE](./LICENSE). Individual skill folders may carry their own license file if they were imported from a separately-licensed source.

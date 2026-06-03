# uristocrat/skills

**Production-ready [Claude Code](https://claude.ai/code) skills and agents you can install in 30 seconds.**

Browse the live catalog at **[skills.uristocrat.com](https://skills.uristocrat.com)** · Built and maintained by [uristocrat](https://uristocrat.com)

---

Claude Code skills extend Claude with focused, repeatable workflows — get a weekly read on your business cashflow, see where your brand shows up in ChatGPT, fix your Ghost site's Google indexing, walk through filing an unemployment claim. One `curl`, and Claude knows how to do the job.

This repo is the source of truth for every skill we publish. Each is MIT-licensed, version-tagged, and ready to drop into Claude Code, Claude Desktop, or any Anthropic-compatible runtime that loads `SKILL.md` files.

## Who this is for

- **End users** who want Claude to handle a specific task end-to-end — no prompting tricks, no glue code. Pick a skill, install it, ask Claude.
- **Product managers** evaluating what Claude skills look like in the wild — real-world scope, packaging, and triggers worth borrowing.
- **Developers** building their own skills and agents — every folder here is a working reference you can fork, study, or PR against.

## What's inside

### Find a skill by what you want to do

| I want to… | Use | Type |
| --- | --- | --- |
| **File for unemployment** after a layoff — all 50 states + DC | [`unemployment-guide/`](./unemployment-guide) | skill |
| **Fix my Ghost blog's Google indexing** automatically (Search Console → diagnose → fix → resubmit) | [`ghost-seo-agent/`](./ghost-seo-agent) | skill |
| **See where my brand shows up in ChatGPT, Perplexity, and Claude** — and what to write to close the gap | [`llm-visibility-agent/`](./llm-visibility-agent) | skill |
| **Get a weekly cashflow pulse** across Mercury, Ramp, and Grasshopper | [`financial-pulse/`](./financial-pulse) | skill + 3 agents |
| **Run buy-side due diligence on a private company** before you buy it (QoE, red-flag matrix, valuation impact) | [`buy-side-diligence/`](./buy-side-diligence) | skill |
| **Chat with my ad and analytics data and get ranked optimization moves** across Google Ads, Meta, TikTok, LinkedIn, GA4, and Stripe | [`ads-copilot/`](./ads-copilot) | skill |
| **Strip the AI tells from my Office docs** before they ship — pipe separators, em dashes, default colors, Sheet1 names, and other machine-generated giveaways in .pptx/.docx/.xlsx | [`office-tells/`](./office-tells) | skill |

More skills land here regularly. **[Watch this repo](https://github.com/uristocrat/skills/subscribe)** or follow the [catalog](https://skills.uristocrat.com) to catch new releases.

## Install in 30 seconds

Every skill installs the same way — one `curl` into `~/.claude/skills/`, then restart Claude Code:

```bash
mkdir -p ~/.claude/skills/<skill-name>
curl -fsSL -o ~/.claude/skills/<skill-name>/SKILL.md \
  https://raw.githubusercontent.com/uristocrat/skills/v1.0.0/<skill-name>/SKILL.md
```

The fastest path is **[skills.uristocrat.com](https://skills.uristocrat.com)** — every skill's catalog page generates the exact pinned install command for you, copy-paste ready.

> Some skills (e.g. `financial-pulse`) ship as plugins with nested `skills/` and `agents/` directories. The catalog handles the path automatically; if you're installing by hand, follow that skill's README.

## Why these skills exist

Every skill in this repo solves a problem we actually had at uristocrat — then we generalized it so anyone can use it. That's the bar: it has to be useful on day one, not a demo. If a skill stops being useful, we deprecate it instead of letting it rot.

We pin every install URL to a tagged release (never `main`), so the skill you install today behaves the same way next month.

## For skill authors

This repo doubles as a working reference for how we package skills:

- **`SKILL.md` with rich YAML frontmatter** — name, description, and trigger phrases that Claude actually matches against
- **One folder per skill**, supporting files in `references/`, `agents/`, `scripts/`
- **Tagged releases** — `v1.0.0`, `v1.1.0`, etc. — with a generated [`index.json`](./index.json) the catalog consumes
- **Contribution path** in [CONTRIBUTING.md](./CONTRIBUTING.md): new skill = new top-level folder, one PR

Cutting a release:

1. Bump `version` in frontmatter for any changed `SKILL.md`.
2. Tag: `git tag v1.x.0 && git push origin v1.x.0`.
3. Rebuild the index: `node scripts/build-index.mjs --tag v1.x.0` and commit.
4. Update the catalog entries in [uristocrat/uristocrat-skills](https://github.com/uristocrat/uristocrat-skills) to point at the new tag.

## License

MIT — see [LICENSE](./LICENSE). Individual skill folders may carry their own license file if imported from a separately-licensed source.

---

**Questions, bug reports, or skill ideas?** Open an [issue](https://github.com/uristocrat/skills/issues) or PR. We read every one.

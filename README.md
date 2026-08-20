# Anlo-Ventures/skills-and-agents-library

**Skills that make [Claude Code](https://claude.ai/code) more capable. Install one with a single command.**

Browse the live catalog at **[skillsandagents.co](https://skillsandagents.co)** · Built and maintained by [Skills and Agents Co](https://skillsandagents.co)

---

Each skill adds a specific capability to Claude: check your business cashflow, see where your brand shows up in ChatGPT, fix your Ghost site's Google indexing, walk through filing an unemployment claim. One install, and Claude instantly knows how to do the job.

This repo is the source of truth for every skill we publish. Each is MIT-licensed, version-tagged, and ready to drop into Claude Code, Claude Desktop, or any Anthropic-compatible runtime that loads `SKILL.md` files.

## Install the plugin marketplace

Add the marketplace once, then install any plugin from it:

```bash
/plugin marketplace add Anlo-Ventures/skills-and-agents-library
```

```bash
/plugin install financial-pulse@skills-and-agents
```

Two plugins ship today. `financial-pulse` gives you a cashflow pulse across Mercury, Ramp, and Grasshopper. `product-builder` bundles code review, PR summaries, research briefs, competitor intel, and document drafting.

## Who this is for

- **End users** who want Claude to handle a specific task end-to-end — no prompting tricks, no glue code. Pick a skill, install it, ask Claude.
- **Product managers** evaluating what Claude skills look like in the wild — real-world scope, packaging, and triggers worth borrowing.
- **Developers** building their own skills and agents — every folder here is a working reference you can fork, study, or PR against.

## What's inside

### Find a skill by what you want to do

| I want to… | Use | Type |
| --- | --- | --- |
| **Fix my Ghost blog's Google indexing** automatically (Search Console → diagnose → fix → resubmit) | [`ghost-seo-agent/`](./ghost-seo-agent) | agent |
| **See where my brand shows up in ChatGPT, Perplexity, and Claude** — and what to write to close the gap | [`llm-visibility-agent/`](./llm-visibility-agent) | agent |
| **Get a weekly cashflow pulse** across Mercury, Ramp, and Grasshopper | [`financial-pulse/`](./financial-pulse) | skill + 3 agents |
| **Run buy-side due diligence on a private company** before you buy it (QoE, red-flag matrix, valuation impact) | [`buy-side-diligence/`](./buy-side-diligence) | skill |
| **Chat with my ad and analytics data and get ranked optimization moves** across Google Ads, Meta, TikTok, LinkedIn, GA4, and Stripe | [`ads-copilot/`](./ads-copilot) | skill |
| **Strip the AI tells from my Office docs** before they ship — pipe separators, em dashes, default colors, Sheet1 names, and other machine-generated giveaways in .pptx/.docx/.xlsx | [`office-tells/`](./office-tells) | skill |
| **Actually understand the code Claude just wrote** — a teaching loop that quizzes you on the problem, solution, design decisions, and edge cases until you've demonstrably got it | [`learn-quiz/`](./learn-quiz) | skill |
| **Turn a meeting transcript into structured meeting memory** — a dated meeting note, one mention line per person/company you track, and a recap email drafted (never sent) | [`meeting-scribe/`](./meeting-scribe) | skill |
| **Prep for an upcoming meeting** — read your calendar export, match attendees and companies against the people/companies you track, and get a dated brief with their full mention history before you walk in | [`calendar-agent/`](./calendar-agent) | skill |

More skills land here regularly. **[Watch this repo](https://github.com/Anlo-Ventures/skills-and-agents-library)** or follow the [catalog](https://skillsandagents.co) to catch new releases.

## Install in 30 seconds

Every skill installs the same way — one `curl` into `~/.claude/skills/`, then restart Claude Code:

```bash
mkdir -p ~/.claude/skills/<skill-name>
curl -fsSL -o ~/.claude/skills/<skill-name>/SKILL.md \
  https://raw.githubusercontent.com/Anlo-Ventures/skills-and-agents-library/v1.23.0/<skill-name>/SKILL.md
```

The fastest path is **[skillsandagents.co](https://skillsandagents.co)** — every skill's catalog page generates the exact pinned install command for you, copy-paste ready.

> Some skills (e.g. `financial-pulse`) ship as plugins with nested `skills/` and `agents/` directories. The catalog handles the path automatically; if you're installing by hand, follow that skill's README.

## Install via skills.sh

These skills are also installable through [skills.sh](https://skills.sh), the open skills registry. Install the whole catalog at once:

```bash
npx skills add Anlo-Ventures/skills-and-agents-library
```

Or pull a single skill by its slug:

```bash
npx skills add Anlo-Ventures/skills-and-agents-library --skill <slug>
```

Available skills and their slugs:

- `unemployment-guide` (file for unemployment, all 50 states + DC)
- `learn-quiz` (make Claude teach you the work until you actually understand it)
- `ghost-seo-agent` (diagnose and fix Ghost Google indexing)
- `office-tells` (strip the AI tells from .pptx/.docx/.xlsx)
- `buy-side-diligence` (run buy-side due diligence on a private company)
- `llm-visibility-agent` (see where your brand shows up across ChatGPT, Perplexity, and Claude)
- `financial-pulse` (weekly cashflow pulse across Mercury, Ramp, and Grasshopper)
- `ads-copilot` (chat with your ad and analytics data for ranked optimization moves)
- `meeting-scribe` (turn a meeting transcript into structured meeting memory, inspired by USV)
- `calendar-agent` (prep briefs for upcoming meetings against your tracked people/companies, inspired by USV)

The full catalog, with per-skill pages and pinned install commands, lives at [skillsandagents.co](https://skillsandagents.co/). Skills surface on skills.sh automatically through install telemetry, so there is no registration step on our end.

## Why these skills exist

Every skill in this repo solves a problem we actually had running our own companies — then we generalized it so anyone can use it.
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

## License

MIT — see [LICENSE](./LICENSE). Individual skill folders may carry their own license file if imported from a separately-licensed source.

---

**Questions, bug reports, or skill ideas?** Open an [issue](https://github.com/Anlo-Ventures/skills-and-agents-library/issues) or PR. We read every one.

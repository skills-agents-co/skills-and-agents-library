# Ghost SEO Agent

A free Claude Code skill for Ghost publishers. Runs a fully autonomous SEO audit — pulls non-indexed URLs from Google Search Console, diagnoses each one, applies metadata fixes directly to your Ghost posts, and submits re-indexing requests. No CSV exports, no clicking through dashboards.

Questions or issues: **seo@uristocrat.com**

---

## What it does

- Logs into Google Search Console and pulls your non-indexed and excluded URLs
- Cross-references them against your Ghost post list via Ghost MCP
- Fixes metadata gaps automatically: missing meta descriptions, excerpts, meta titles, and members-only post teasers
- Submits re-indexing requests for every post it fixes
- Audits Ghost-specific structural issues (tag/author archives, paginated pages, sitemaps, canonical tags, HTTPS config, sparse tags, non-WebP images)
- Detects thin posts and isolated posts with no internal links
- Includes a migration audit mode for publishers moving from Substack or WordPress

---

## Requirements

- **[Claude Code](https://claude.ai/code)** — the CLI or desktop app
- **Ghost MCP** — connects Claude to your Ghost Admin API so it can read and edit posts
- **Browser tool** — Claude in Chrome (browser extension) or Cowork for full autonomous mode

---

## Installation

### 1. Connect Ghost MCP to Claude Code

Ghost MCP lets Claude read and edit your Ghost posts via the Admin API.

**Install the Ghost MCP server:**

```bash
npm install -g @tryghost/mcp-server
```

**Get your Ghost Admin API key:**

1. Log into Ghost Admin → Settings → Integrations
2. Click "Add custom integration" → name it `Claude SEO Agent`
3. Copy the **Admin API Key**

**Add Ghost MCP to your Claude Code config** (`~/.claude/claude.json` or via `claude mcp add`):

```json
{
  "mcpServers": {
    "ghost-mcp": {
      "command": "ghost-mcp",
      "args": [],
      "env": {
        "GHOST_URL": "https://your-ghost-site.com",
        "GHOST_ADMIN_API_KEY": "your-admin-api-key-here"
      }
    }
  }
}
```

Restart Claude Code after saving.

### 2. Install the skill

Point Claude Code at this repo's `SKILL.md`:

```bash
claude skills add https://raw.githubusercontent.com/uristocrat/ghost-seo-agent/main/SKILL.md
```

Or clone the repo and add it locally:

```bash
git clone https://github.com/uristocrat/ghost-seo-agent.git
claude skills add ./ghost-seo-agent/SKILL.md
```

### 3. Run it

Open Claude Code and say:

```
run SEO audit for my Ghost site
```

Claude will confirm your site URL and begin the audit.

---

## What the audit covers (10-step workflow)

1. **Authenticate into Google Search Console** and verify your sitemap is submitted correctly
2. **Pull the coverage report** — non-indexed and excluded URLs, organized by issue type
3. **Cross-reference with Ghost** — match each URL to its post record and flag metadata gaps
4. **Diagnose each URL** — URL Inspection Tool check, crawl status, noindex tags, rendering issues, and internal link coverage
5. **Apply metadata fixes** — writes meta descriptions, excerpts, meta titles, and members-only teasers directly via Ghost MCP
6. **Submit re-indexing requests** — up to 12/day per Google's rate limit, prioritized by recency and keyword value
7. **Structural issues audit** — detects tag/author archive noindex gaps, paginated pages, missing `{{ghost_head}}`, HTTP canonicals, and sparse tags; surfaces exact theme-level code fixes
8. **Generate a full SEO report** — summary stats, fixed posts table, structural issues with priority ratings, content flags, tag quality table
9. **72-hour follow-up** (autonomous mode) — checks which URLs got indexed and escalates any that didn't
10. **Migration audit mode** — redirect coverage check and canonical integrity audit for publishers migrating from Substack or WordPress

### What it fixes automatically
- Missing meta descriptions
- Missing custom excerpts
- Long post titles (generates a shorter `meta_title`)
- Members-only posts with no excerpt (adds a teaser so Googlebot has something to index)

### What it flags for manual action
- Thin content (under 300 words) — requires editorial work
- Missing feature images — requires editorial judgment
- Non-WebP images — requires re-uploading outside Ghost MCP
- Isolated posts with no internal links — surfaces suggested link targets
- Theme-level structural issues — provides exact Handlebars code to add

---

## Coming soon

**Schema injection** — automatic structured data for FAQ, HowTo, and Review post types. The agent will detect eligible posts and inject JSON-LD schema blocks via Ghost's code injection, without requiring theme edits.

---

## License

MIT — free to use, fork, and modify.

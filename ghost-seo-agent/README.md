# Ghost SEO Agent

A free Claude Code skill for Ghost publishers. Runs a fully autonomous SEO audit — pulls non-indexed URLs from Google Search Console, diagnoses each one, applies metadata fixes directly to your Ghost posts, and submits re-indexing requests. No CSV exports, no clicking through dashboards.

**Need help?** Email **contact@skillsandagents.co** or visit **[skillsandagents.co](https://skillsandagents.co)**

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

Before you start, you need three things:

1. **[Claude Code](https://claude.ai/code)** — the desktop app or CLI (free tier works)
2. **Ghost MCP server** — a local server that lets Claude talk to your Ghost site
3. **Browser access** — the Claude in Chrome extension for full autonomous mode

---

## Installation

### Step 1 — Install Claude Code

If you don't have Claude Code yet:

1. Go to [claude.ai/code](https://claude.ai/code) and download the desktop app
2. Sign in with your Anthropic account (or create a free one)
3. Open Claude Code and confirm it launches

---

### Step 2 — Install Node.js (if you don't have it)

The Ghost MCP server requires Node.js.

1. Go to [nodejs.org](https://nodejs.org) and download the **LTS** version
2. Run the installer and follow the prompts
3. Verify the install — open Terminal (Mac) or Command Prompt (Windows) and run:

```bash
node --version
```

You should see a version number like `v20.x.x`. If you do, you're good.

---

### Step 3 — Install the Ghost MCP server

The Ghost MCP server is a community-built package that connects Claude to your Ghost Admin API. It supports all the fields this skill uses: metadata, excerpts, feature images, and tags.

Open Terminal and run:

```bash
npm install -g @jgardner04/ghost-mcp-server
```

This installs it globally so Claude Code can find it.

Verify it installed:

```bash
ghost-mcp-server --version
```

---

### Step 4 — Get your Ghost Admin API key

Claude needs an API key to read and edit your posts.

1. Log into your Ghost Admin panel (usually `https://your-site.com/ghost`)
2. Go to **Settings** → **Integrations**
3. Scroll down and click **"Add custom integration"**
4. Name it `Claude SEO Agent` and click **Create**
5. Copy the **Admin API Key** — it looks like a long string of letters and numbers

Keep this key somewhere safe. You'll need it in the next step.

---

### Step 5 — Connect Ghost MCP to Claude Code

Now tell Claude Code how to reach your Ghost site.

**On Mac**, open Terminal and run this command — replacing the placeholders with your actual site URL and API key:

```bash
claude mcp add ghost-mcp -- ghost-mcp-server \
  --url https://your-ghost-site.com \
  --key your-admin-api-key-here
```

**On Windows**, open Command Prompt and run:

```cmd
claude mcp add ghost-mcp -- ghost-mcp-server --url https://your-ghost-site.com --key your-admin-api-key-here
```

To confirm it connected, run:

```bash
claude mcp list
```

You should see `ghost-mcp` in the list with a connected status.

---

### Step 6 — Install the Claude in Chrome extension

The skill uses your browser to log into Google Search Console on your behalf. This requires the Claude in Chrome extension.

1. Open Chrome
2. Go to the [Chrome Web Store](https://chromewebstore.google.com) and search for **"Claude in Chrome"** by Anthropic
3. Click **"Add to Chrome"** and confirm the install
4. Click the extension icon in your browser toolbar and sign in with your Anthropic account

---

### Step 7 — Install this skill

Run this command in Terminal to add the Ghost SEO Agent skill to Claude Code:

```bash
claude skills add https://raw.githubusercontent.com/uristocrat/ghost-seo-agent/main/SKILL.md
```

---

### Step 8 — Run the audit

Open Claude Code and type:

```
run SEO audit for my Ghost site
```

Claude will ask for your site URL and then handle everything from there — logging into Search Console, pulling non-indexed URLs, applying fixes, and submitting re-indexing requests.

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

## Need help?

Email **contact@skillsandagents.co** or visit **[skillsandagents.co](https://skillsandagents.co)**

---

## License

MIT — free to use, fork, and modify.

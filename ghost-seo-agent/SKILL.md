---
name: ghost-seo-agent
description: >
  Autonomously audits, fixes, and re-submits Ghost posts for Google indexing.
  Works for any Ghost publisher. Uses browser access to log into Google Search
  Console, pull non-indexed URLs, diagnose each page, apply fixes via Ghost MCP,
  and request re-crawl — all without manually exporting CSVs or clicking through
  Search Console. Also detects Ghost-specific structural issues (tag/author archives,
  paginated pages, sitemaps, AMP duplicates, HTTPS config, members-only content,
  sparse tags, non-WebP images) and content quality problems (thin posts, isolated
  posts with no internal links). Includes a migration audit mode for publishers
  moving from Substack or WordPress.

  Use this skill whenever a Ghost publisher says "run SEO audit", "fix indexing
  issues", "check what's not indexed", "why aren't my posts showing up in Google",
  "fix Ghost SEO", or any similar phrase about search visibility, indexing, or
  organic traffic on a Ghost site.

  Always use this skill for Ghost SEO work — do not attempt to diagnose or fix
  indexing issues manually without it.

compatibility: "Requires browser tool (Claude in Chrome or Cowork) and ghost-mcp connected to the publisher's Ghost instance. Cowork preferred for scheduled/persistent runs; single-session mode available for on-demand audits."
---

# Ghost SEO Agent

Fully autonomous SEO audit and indexing repair loop for any Ghost-powered site.
Runs end-to-end from Search Console diagnosis through Ghost metadata fixes through
re-crawl submission. Detects structural Ghost SEO issues and surfaces actionable
fixes with exact code.

---

## Setup — Confirm Site URL

Before starting, confirm the target site URL with the publisher:

```
SITE_URL = https://[your-ghost-site.com]
```

All Search Console navigation, sitemap checks, and report links derive from this URL.
If the publisher doesn't specify, ask: "What's your Ghost site URL?"

---

## Execution Modes

### Mode A — Full Autonomous (Cowork + Browser)
Complete loop: Search Console login → audit → diagnose → fix → resubmit → follow-up.
Preferred mode. Use when Cowork and browser tools are available.

### Mode B — Single Session (Browser only, no Cowork)
Same steps as Mode A without the 48-72 hour follow-up loop. Runs to completion
in one session and produces a report artifact.

### Mode C — CSV Input (no browser)
Publisher exports the Coverage report from Search Console as CSV and drops it into
the conversation. Skill handles diagnosis and Ghost fixes, produces a manual
re-indexing checklist. Use only when browser is unavailable.

### Mode D — Migration Audit (Substack / WordPress → Ghost)
Checks redirect coverage, canonical integrity, and URL mapping for publishers
who recently migrated from another platform. See Step 10 for full workflow.

---

## Full Workflow (Mode A — Canonical)

### Step 1 — Authenticate into Google Search Console + Verify Sitemap

Navigate to: `https://search.google.com/search-console`

If not logged in:
- Click "Start now" → sign in with the publisher's Google account
- **Do not enter credentials yourself** — pause and ask the publisher to authenticate,
  then confirm when done before proceeding
- Once authenticated, confirm the `{{SITE_URL}}` property is selected

If both `http://` and `https://` variants exist, always use `https://`.

**Sitemap check (do this immediately after login)**:

Navigate to Search Console → Sitemaps.

| Condition | Action |
|-----------|--------|
| `{{SITE_URL}}/sitemap.xml` submitted and returning 200 | OK, proceed |
| Only `sitemap-posts.xml` submitted | Flag as misconfiguration — root sitemap required |
| Nothing submitted | Submit `{{SITE_URL}}/sitemap.xml` and note in report |
| sitemap.xml returning error | Flag as high-priority structural issue |

Ghost generates a root sitemap at `/sitemap.xml` that links to all sub-sitemaps
(`sitemap-posts.xml`, `sitemap-pages.xml`, etc.). Always submit the root, not a
sub-sitemap — submitting only `sitemap-posts.xml` causes pages and tags to be missed.

---

### Step 2 — Pull the Coverage / Indexing Report

Navigate to: Search Console → Indexing → Pages

Target tabs to check (in order of priority):
1. **"Not indexed"** — primary target
2. **"Excluded"** — secondary, check for "Crawled - currently not indexed"

For each issue category, note:
- Issue type label
- Number of affected URLs
- Representative sample URLs (click through to see the full list)

Export or record the full URL list for the top 2-3 issue categories.
Prioritize content pages (posts) over tag/author/page archive URLs.

---

### Step 3 — Cross-reference with Ghost post list

Use `ghost-mcp:posts_browse` to pull all published posts:

```
status: published
limit: all
fields: id, title, slug, url, published_at, custom_excerpt, feature_image,
        meta_title, meta_description, visibility, html, tags
```

Build a lookup map: `{ slug → post_data }` for efficient matching.

For each non-indexed URL from Step 2:
- Match to its Ghost post record
- Flag if the post has:
  - Missing `meta_description`
  - Missing `custom_excerpt`
  - Missing `feature_image`
  - Title > 60 characters and no `meta_title`
  - HTML word count < 300 words (strip tags, count words)
  - `visibility` set to `members` or `paid` with no `custom_excerpt` — Googlebot
    cannot access gated content; a free preview excerpt is the only indexable signal
  - `feature_image` URL that doesn't end in `.webp` — non-WebP format hurts LCP scores

---

### Step 4 — Diagnose each non-indexed URL

#### 4a — URL Inspection Tool

For each flagged URL, use the URL Inspection Tool in Search Console:

Path: Search Console → URL Inspection → paste URL → Enter

Check:
- **Coverage status**: "URL is not on Google" vs. "URL is on Google"
- **Last crawl date**: never crawled = discovery problem; crawled but not indexed = quality signal problem
- **Crawl allowed**: confirm robots.txt isn't blocking
- **Indexing allowed**: confirm no noindex tag
- **Page fetch**: click "Test Live URL" → "View Tested Page" → verify rendered HTML
  matches expected content (Ghost JS rendering issues can cause thin-content flags)

Categorize each URL:

| Category | Likely Cause | Fix Type |
|---|---|---|
| Never crawled | Not linked internally, sitemap gap | Internal links + sitemap |
| Crawled, not indexed — metadata thin | No meta description, no excerpt, no feature image | Metadata fixes (Step 5) |
| Crawled, not indexed — content thin | Post under 300 words, no unique value | Flag for editorial review |
| Members-only, no preview | Gated content invisible to Googlebot | Add excerpt (Step 5, Fix E) |
| Noindex tag | Ghost tag/author archive pages | Structural fix (Step 7) |
| Blocked by robots | Ghost config issue | Structural fix (Step 7) |
| Duplicate canonical | Missing or wrong canonical tag | Structural fix (Step 7) |
| AMP alternate | `/url/amp/` duplicate — expected Ghost behavior | No action needed |
| JS render issue | Ghost content not rendering for Googlebot | Escalate to publisher |

#### 4b — Internal Link Check (for "never crawled" posts)

For each post in the "never crawled" bucket, scan the `html` field of all other
published posts (from Step 3) for links containing the post's slug.

If zero other posts link to it: flag as **isolated post**.

Identify 2-3 related posts by tag overlap as candidates for adding an internal link.
Note in report as "manual editorial action required" — do not auto-edit post bodies.

---

### Step 5 — Apply Ghost metadata fixes (automated)

For each post in the "Crawled, not indexed" bucket with metadata gaps, apply fixes
via Ghost MCP. Do not apply fixes to thin-content posts without metadata issues —
adding a meta description to a 150-word post won't fix the underlying quality problem.

#### Fix A — Missing meta description
If `meta_description` is null or empty:

Generate a meta description:
- 140-155 characters
- Includes the primary keyword (infer from title + first paragraph)
- Specific — names the product, player, team, or topic
- Does not start with "In this post" or "Learn how"

Apply:
```
ghost-mcp:posts_edit → id: [post_id], meta_description: [generated]
```

#### Fix B — Missing custom excerpt
If `custom_excerpt` is null:

Generate a 1-2 sentence excerpt that:
- Leads with the most specific/interesting fact from the post
- Is distinct from the meta description (not a copy-paste)
- Under 300 characters

Apply:
```
ghost-mcp:posts_edit → id: [post_id], custom_excerpt: [generated]
```

#### Fix C — Title too long
If `title` > 60 characters and `meta_title` is null:

Generate a meta title that:
- Is under 60 characters
- Preserves the primary keyword
- Doesn't truncate mid-word in Google's SERP display

Apply:
```
ghost-mcp:posts_edit → id: [post_id], meta_title: [shortened title]
```

#### Fix D — No feature image (flag only, don't auto-apply)
If `feature_image` is null: add to the manual fix list. Do not attempt to
auto-assign images — image selection requires editorial judgment.

#### Fix E — Members-only post with no excerpt
If `visibility` is `members` or `paid` and `custom_excerpt` is null:

Generate a 1-2 sentence teaser excerpt that:
- Describes what the post covers without giving away the full content
- Functions as a standalone hook for search results
- Under 300 characters

Apply:
```
ghost-mcp:posts_edit → id: [post_id], custom_excerpt: [generated teaser]
```

#### Fix F — Feature image not WebP (flag only)
If `feature_image` URL doesn't end in `.webp`: add to manual fix list with note
"Re-upload as WebP to improve LCP score." Do not attempt to convert or re-upload
images — this requires editorial action outside Ghost MCP.

---

### Step 6 — Request re-indexing in Search Console

For every post where Ghost fixes were successfully applied in Step 5:

Navigate to Search Console URL Inspection tool.
For each fixed URL:
1. Paste the URL → Enter
2. Click "Request Indexing"
3. Wait for confirmation modal
4. Note the timestamp

**Rate limit**: Google allows ~10-12 indexing requests per day per property.
If more than 12 posts need resubmission, prioritize by:
1. Posts published in the last 30 days
2. Posts with the most specific/high-value keywords in the title
3. Longer posts (higher word count = stronger quality signal)

Queue the remainder for the next session.

---

### Step 7 — Ghost structural issues audit

Some issues cannot be fixed via Ghost MCP and require theme-level changes.
Detect these automatically and surface exact fixes with code.

#### 7a — Tag and author archive pages

**Detect**: Any `/tag/*/` or `/author/*/` URLs appearing in the GSC "Not indexed"
or "Excluded" lists, OR a high ratio of excluded pages to indexed pages.

**Why it matters**: Ghost indexes these by default. They contain only post lists —
no original content — which creates thin-content signals and wastes crawl budget.

**Fix** (add to theme templates):

`tag.hbs` and `author.hbs`:
```handlebars
{{#contentFor "meta"}}
<meta name="robots" content="noindex, nofollow">
{{/contentFor}}
```

Or in `default.hbs` as a conditional:
```handlebars
{{#is "tag, author"}}
<meta name="robots" content="noindex, nofollow">
{{/is}}
```

Include in report as: **High priority.**

#### 7b — Paginated archive pages (/page/2/, /page/3/, etc.)

**Detect**: Any `/page/[number]/` URLs in GSC coverage.

**Fix — Option A** (noindex in `default.hbs`):
```handlebars
{{#if pagination.prev}}
<meta name="robots" content="noindex" />
{{/if}}
```

**Fix — Option B** (redirect via `redirects.json`):
```json
[
  {
    "from": "/page/[0-9]+/",
    "to": "/",
    "permanent": true
  }
]
```

Include in report as: **Medium priority.**

#### 7c — AMP alternate pages

**Detect**: Any `/*/amp/` URLs in GSC "Excluded" with reason "Alternate page with
proper canonical tag."

This is expected Ghost behavior. Google indexes the original and excludes the AMP
duplicate. No action needed.

Include in report as: **Expected behavior — no action required.**

#### 7d — Missing {{ghost_head}} in custom theme

**Detect**: View-source on a sample post URL. Check that `<head>` contains a
`<link rel="canonical">` tag and a JSON-LD schema block — both injected by `{{ghost_head}}`.

If absent: the theme is missing `{{ghost_head}}`.

**Fix**: Add to the theme's `default.hbs`:
```handlebars
<head>
  ...
  {{ghost_head}}
</head>
```

Include in report as: **Critical — all canonical and schema injection is broken
until this is fixed.**

#### 7e — HTTPS canonical check

**Detect**: View-source on any published post. Confirm `<link rel="canonical">`
uses `https://` not `http://`. An HTTP canonical quietly splits crawl equity and
is a common misconfiguration on self-hosted Ghost installs.

If HTTP canonical found: flag as high priority. Fix is updating the Ghost config
`url` property to `https://{{SITE_URL}}` and restarting Ghost.

Include in report as: **High priority — if self-hosted.**

#### 7f — Members-only content with no excerpt

**Detect**: From Step 3, posts where `visibility` is `members` or `paid` and
`custom_excerpt` is null (and not already fixed in Step 5).

**Why it matters**: Googlebot cannot authenticate to view gated content. The excerpt
is the only part of the post that's indexable. No excerpt = invisible to search engines.

Fix is automated in Step 5 Fix E. Any remaining unfixed instances should be flagged here.

Include in report as: **High priority.**

#### 7g — Tag quality audit (sparse tags)

**Detect**: From the `tags` field on posts in Step 3, count posts per tag.
Flag any tag with fewer than 5 posts.

**Why it matters**: Tags with 1-4 posts generate thin archive pages that waste crawl
budget and add no ranking value.

**Options** (surface all three, let the publisher choose):
1. Merge the tag into a broader existing tag
2. Add a substantive description to the tag (in Ghost Admin → Tags → [tag] → Description)
3. Noindex the tag archive (see 7a fix — applies per-tag via `tag.hbs`)

Include in report as: **Medium priority — list affected tags by post count.**

---

### Step 8 — Produce the SEO Report

Generate a clean, readable report artifact.

**Header**
```
GHOST SEO AUDIT
Site: {{SITE_URL}}
Run: [date and time]
Mode: [Full Autonomous / Single Session / CSV Input / Migration Audit]
```

**Summary stats**
- Total non-indexed URLs found
- Metadata fixes applied (meta descriptions, excerpts, meta titles, members excerpts)
- Re-indexing requests submitted
- Structural issues flagged (require theme edits)
- Thin content posts flagged (require editorial review)
- Isolated posts (require internal link additions)
- Non-WebP images flagged
- Sparse tags flagged
- Posts queued for next session

**Fixed posts table**
| Post title | Issue | Fix applied | Reindex requested |
|---|---|---|---|
| [title] | Missing meta description | Applied | Yes |

**Structural issues (theme edits required)**
Numbered list with:
- Issue description
- Affected URL count
- Exact fix (code snippet where applicable)
- Priority: Critical / High / Medium / Low

**Content issues (editorial review required)**
- Thin content: [title] — [word count] words
- Isolated posts: [title] → suggested link targets: [post A], [post B]
- Missing feature images: [title list]
- Non-WebP images: [title list]

**Tag quality issues**
| Tag | Post count | Recommendation |
|---|---|---|
| [tag] | 2 | Merge into [broader tag] or add description |

**Sitemap status**
`✅ sitemap.xml submitted and healthy` or `❌ [issue]`

**HTTPS status**
`✅ Canonicals use https://` or `❌ HTTP canonical found — fix Ghost config URL`

---

### Step 9 — Schedule follow-up (Mode A only)

72 hours after the audit, return to Search Console URL Inspection for each URL
where indexing was requested.

Check if status changed to "URL is on Google."

- **Indexed**: mark as resolved in follow-up report
- **Still not indexed**: escalate — fix didn't take or deeper quality signal issue

Produce a brief follow-up: "Ghost SEO Audit Follow-up — [date]" with a
resolved/pending/escalated table.

---

### Step 10 — Migration Audit (Mode D only)

Use when the publisher has recently migrated from Substack, WordPress, or another platform.

#### 10a — Get old platform URL

Ask: "What was your old site URL?" (e.g., `yoursite.substack.com` or `old-wordpress.com`)

#### 10b — Pull Ghost post slugs

Use `ghost-mcp:posts_browse` to get all published posts with `slug` and `url` fields.

#### 10c — Check redirect coverage

Ask the publisher to share their `redirects.json` / `redirects.yaml` file content.

For each Ghost post slug, check if a corresponding redirect from the old URL exists.

**Expected Substack pattern**: `https://[pub].substack.com/p/[slug]` → `https://{{SITE_URL}}/[slug]`

Flag posts with no redirect configured.

#### 10d — Produce redirect mapping template

For all uncovered posts, output a ready-to-use `redirects.json` block:

```json
[
  {
    "from": "/p/[old-slug]",
    "to": "/[new-slug]",
    "permanent": true
  }
]
```

#### 10e — Check for reverse canonicals

View-source on 3-5 Ghost posts. Confirm `<link rel="canonical">` points to
`{{SITE_URL}}/[slug]`, not the old platform URL. If any canonical points back to
the old platform, flag as critical — this leaks authority and prevents Ghost posts
from ranking.

---

## Ghost MCP Error Handling

If `ghost-mcp:posts_edit` fails for a specific post:
- Log the failure with post ID and error message
- Continue to the next post — do not halt the entire run
- Include failed edits in the report under "Manual fixes required"

If Ghost MCP is completely unavailable:
- Complete Steps 1-4 (diagnosis) using browser only
- Skip Steps 5-6 (fixes)
- Produce a diagnosis-only report with a manual fix checklist

---

## Browser Navigation Fallbacks

If Search Console UI has changed:
- Use the search bar within Search Console to find "Pages" or "Coverage" report
- Adapt to UI changes — do not fail because a menu label changed

If Google requires re-authentication mid-session:
- Pause and notify the publisher
- Do not attempt to enter credentials
- Resume from the last completed step after the publisher re-authenticates

---

## Scope Boundaries

**The Ghost SEO agent will:**
- Fix meta descriptions, meta titles, custom excerpts, and members-only excerpts via Ghost MCP
- Submit re-indexing requests in Search Console
- Diagnose and report structural issues with exact code fixes
- Detect thin content, isolated posts, non-WebP images, and sparse tags
- Check sitemap submission, canonical tag presence, and HTTPS config
- Run migration redirect audits

**The Ghost SEO agent will NOT:**
- Edit post body content
- Change post URLs/slugs
- Modify Ghost theme files directly (surfaces code fixes for the publisher)
- Delete or unpublish posts
- Convert or re-upload images

---

## Need Help?

If you're a Ghost publisher running into issues with this skill, reach out:

- Email: **skills@uristocrat.com**
- More skills and documentation: **[skills.uristocrat.com](https://skills.uristocrat.com)**

---

## Trigger Phrases

- "run SEO audit for my Ghost site"
- "why aren't my Ghost posts indexed"
- "check my Ghost indexing"
- "fix Ghost SEO"
- "run the SEO audit"
- "fix the indexing issues"
- "check what's not indexed"
- "why aren't my posts showing up in Google"
- "my Ghost posts aren't ranking"
- "do a migration SEO check" (triggers Mode D)

---

**More from SkillsAndAgents.co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/ghost-seo-agent/).

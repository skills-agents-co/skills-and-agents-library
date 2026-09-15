# Full Workflow (Mode A — Canonical)

Loaded by Modes A, B, and C.

- **Mode B** runs this in full except Step 9 (the 48-72 hour follow-up loop) — Mode B produces a report and stops after Step 8.
- **Mode C** replaces Steps 1-2 with a pasted Coverage-report CSV, runs Steps 3-5 as written, and replaces Step 6 with a manual re-indexing checklist (no browser to submit requests). Mode C does not run Step 7 as written here — Step 7 needs a browser (view-source, Search Console) and Mode C has none. This is a known, pre-existing gap, not something to work around.

See `../SKILL.md`'s Safety & Cost Rules for the credential-entry rule and the indexing rate limit — both apply here and are not repeated per-step.

---

### Step 1 — Authenticate into Google Search Console + Verify Sitemap

Navigate to: `https://search.google.com/search-console`

If not logged in:
- Click "Start now" → sign in with the publisher's Google account
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
| Crawled, not indexed — metadata thin | No meta description, no excerpt, no feature image | Metadata fixes (see `fix-recipes.md`) |
| Crawled, not indexed — content thin | Post under 300 words, no unique value | Flag for editorial review |
| Members-only, no preview | Gated content invisible to Googlebot | Add excerpt (`fix-recipes.md`, Fix E) |
| Noindex tag | Ghost tag/author archive pages | Structural fix (see `structural-audits.md`) |
| Blocked by robots | Ghost config issue | Structural fix (see `structural-audits.md`) |
| Duplicate canonical | Missing or wrong canonical tag | Structural fix (see `structural-audits.md`) |
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
via Ghost MCP. See `fix-recipes.md` for the six fix recipes (A-F).

---

### Step 6 — Request re-indexing in Search Console

For every post where Ghost fixes were successfully applied in Step 5:

Navigate to Search Console URL Inspection tool.
For each fixed URL:
1. Paste the URL → Enter
2. Click "Request Indexing"
3. Wait for confirmation modal
4. Note the timestamp

If more than 12 posts need resubmission (see the rate limit in Safety & Cost Rules),
prioritize by:
1. Posts published in the last 30 days
2. Posts with the most specific/high-value keywords in the title
3. Longer posts (higher word count = stronger quality signal)

Queue the remainder for the next session.

**Mode C variant**: no browser, so this step becomes a manual checklist instead —
list each fixed URL and instruct the publisher to submit it themselves via
Search Console's URL Inspection tool, in the same priority order above.

---

### Step 7 — Ghost structural issues audit

Some issues cannot be fixed via Ghost MCP and require theme-level changes.
See `structural-audits.md` for the full set of checks (7a-7g).

Not run in Mode C — this step needs a browser (Search Console + view-source) and
Mode C has none. Pre-existing gap; not fixed by this restructuring.

---

### Step 8 — Produce the SEO Report

See `output-template.md` for the report structure and header format.

---

### Step 9 — Schedule follow-up (Mode A only)

72 hours after the audit, return to Search Console URL Inspection for each URL
where indexing was requested.

Check if status changed to "URL is on Google."

- **Indexed**: mark as resolved in follow-up report
- **Still not indexed**: escalate — fix didn't take or deeper quality signal issue

Produce a brief follow-up: "Ghost SEO Audit Follow-up — [date]" with a
resolved/pending/escalated table.

Mode B skips this step entirely — no follow-up loop, no Cowork persistence.

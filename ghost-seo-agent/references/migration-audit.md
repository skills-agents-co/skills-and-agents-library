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

#### Report

Produce the report using the header, summary stats, and findings-table format in
`references/output-template.md` (Step 8), with `Mode: Migration Audit`.

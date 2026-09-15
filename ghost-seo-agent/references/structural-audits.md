## Ghost structural issues audit (Step 7)

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

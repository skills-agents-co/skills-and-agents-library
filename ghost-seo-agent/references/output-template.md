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

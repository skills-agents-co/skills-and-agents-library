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

## Safety & Cost Rules

These apply across every mode that touches them — not repeated per-step in the reference files.

- **Credential entry**: Never enter credentials yourself in Google Search Console or anywhere else. Pause and ask the publisher to authenticate, then confirm when done before proceeding.
- **Indexing rate limit**: Google allows ~10-12 indexing requests per day per property. See `references/workflow-steps.md` Step 6 for the prioritization order when more posts need resubmission than the daily limit allows.
- **Thin-content fix gate**: Do not apply metadata fixes to thin-content posts that have no metadata issues — adding a meta description to a 150-word post won't fix the underlying quality problem. Flag it for editorial review instead.

---

## Execution Modes

Modes A, B, and C all load `references/workflow-steps.md`, which in turn points
to `references/fix-recipes.md`, `references/structural-audits.md`, and
`references/output-template.md` at the steps that need them — those three files
are reached through `workflow-steps.md`, not named directly by a mode entry
below.

### Mode A — Full Autonomous (Cowork + Browser)
Complete loop: Search Console login → audit → diagnose → fix → resubmit → follow-up.
Preferred mode. Use when Cowork and browser tools are available.
Loads: `references/workflow-steps.md` (Steps 1-9 in full).

### Mode B — Single Session (Browser only, no Cowork)
Same steps as Mode A without the 48-72 hour follow-up loop. Runs to completion
in one session and produces a report artifact.
Loads: `references/workflow-steps.md` (Steps 1-8; skip Step 9 — no follow-up loop).

### Mode C — CSV Input (no browser)
Publisher exports the Coverage report from Search Console as CSV and drops it into
the conversation. Skill handles diagnosis and Ghost fixes, produces a manual
re-indexing checklist. Use only when browser is unavailable.
Loads: `references/workflow-steps.md` — Steps 1-2 are replaced by the pasted CSV,
Steps 3-5 run as written, Step 6 becomes a manual checklist (no browser to submit
requests). Step 7 is not run in this mode — it needs a browser and Mode C has
none; this is a known, pre-existing gap, not something this restructuring fixes.
Step 8 runs as written (the report); Step 9 does not apply (no follow-up loop).

### Mode D — Migration Audit (Substack / WordPress → Ghost)
Checks redirect coverage, canonical integrity, and URL mapping for publishers
who recently migrated from another platform.
Loads: `references/migration-audit.md`, which also points to
`references/output-template.md` for the report format. Shares no other
reference file with Modes A/B/C.

---

## Ghost MCP Error Handling & Browser Fallbacks

Every mode reads this section's pointer, including Mode D. See
`references/error-handling.md` for MCP failure handling and Search Console
UI-change fallbacks.

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

- Email: **contact@skillsandagents.co**
- More skills and documentation: **[skillsandagents.co](https://skillsandagents.co)**

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

## Eval Contract

### Spec

A correct run produces a diagnosis-then-fix report for a Ghost site: every non-indexed URL is categorized by its actual cause (never crawled vs crawled-not-indexed vs structural), every recommendation is specific and actionable with the exact Ghost field or theme code to change, meta-tag and excerpt coverage gaps are named per post, and structural issues (tag/author archives, sitemap, canonical, HTTPS, members-only excerpts) are surfaced with priority labels. The report distinguishes what was auto-fixed via Ghost MCP from what needs editorial or theme action, and it never recommends a change that would harm rankings (for example noindexing a content post, or editing a post body it was told not to touch).

### Rubric

Score each dimension 0 or 1, total out of 8. Run the hard-fail gate first.

**Hard-fail gate (check before scoring):** If the run recommends an action that would harm rankings or remove live content (noindexing a published content post, deleting or unpublishing a post, changing a post slug, or pointing a canonical at the wrong URL), the run is an automatic fail regardless of total score.

1. **Cause diagnosis** (weight 1) — Pass: each non-indexed URL is tied to a specific cause from the categorization table. Fail: URLs are listed without a cause, or the cause is a guess.
2. **Recommendation specificity** (weight 1) — Pass: every recommendation names the exact Ghost field or theme file and gives the concrete change. Fail: vague advice like "improve SEO" or "add metadata" with no target.
3. **Meta-tag coverage** (weight 1) — Pass: meta description, meta title, and excerpt gaps are checked and reported per affected post. Fail: metadata coverage not assessed.
4. **Structural audit completeness** (weight 1) — Pass: sitemap submission, canonical presence, HTTPS canonical, and archive-page handling are all checked. Fail: any of these four skipped without reason.
5. **Auto-fix vs manual separation** (weight 1) — Pass: report clearly splits MCP-applied fixes from editorial/theme actions. Fail: the two are blended so the publisher can't tell what's done.
6. **Members-only excerpt handling** (weight 1) — Pass: gated posts with no excerpt are flagged because Googlebot can't see gated content. Fail: members-only posts treated like public posts.
7. **Priority labeling** (weight 1) — Pass: structural issues carry Critical/High/Medium/Low labels. Fail: issues listed flat with no priority.
8. **Scope discipline** (weight 1) — Pass: does not edit post bodies, change slugs, or modify theme files directly; surfaces code instead. Fail: takes an out-of-scope write action.

**Score to action:** 8/8 ship. 6 to 7 acceptable, note the gap. 4 to 5 borderline, flag for human review. 0 to 3 bad, root-cause. Any hard-fail gate trip is fail regardless of total.

### Self-Test

**Scenario A — Coverage report shows a published 1,200-word post in "Crawled - currently not indexed" with no meta description and no custom excerpt.**
- The output MUST categorize this as a metadata-thin crawled-not-indexed case, not a discovery problem.
- The output MUST recommend setting `meta_description` and `custom_excerpt` on that specific post.
- The output MUST NOT recommend noindexing the post.
- The output MUST NOT recommend editing the post body text.

**Scenario B — A `/tag/sneakers/` archive URL and a members-only post with no excerpt both appear in the non-indexed list.**
- The output MUST flag the tag-archive URL as a structural issue with a noindex theme fix, with a priority label.
- The output MUST flag the members-only post as needing a teaser excerpt because gated content is invisible to Googlebot.
- The output MUST NOT recommend noindexing the members-only content post itself.

**Scenario C — View-source on a sample post shows the canonical tag uses `http://` instead of `https://`.**
- The output MUST flag the HTTP canonical as a high-priority structural issue.
- The output MUST point the fix at the Ghost config `url` property, not at editing individual posts.
- The output MUST NOT silently ignore the protocol mismatch.

### Version

1.0.0

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/ghost-seo-agent/).


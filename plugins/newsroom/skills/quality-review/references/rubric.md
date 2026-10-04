# Quality rubric

The quality review scores each post against this rubric. Voice comes first, because voice is what a reader notices before anything else. Take the voice rules, title rules, tags, and verticals from the publication profile. The rules below apply to every publication.

## What a good post does

Present the facts clearly so the reader gets what they came for without the noise around it. Value comes from subtraction. A post should answer the reader's core question completely enough that the source stops being necessary for that question. Sources stay linked for verification and depth.

## Gate 1: headline

Run this check before scoring. The headline states the fact that happened, and nothing else.

- No `<fact>: <why it matters>` split, and no `<fact>. <framing>` split.
- No "what this means" tail, no question title, no quality words such as "biggest" or "historic" unless the fact is a record and the title says so.
- Two clauses are fine when both are facts: "Company A buys Company B, Company C cuts 200 jobs".
- If the profile has its own title rules, a title that breaks them also fails this gate.

A failing headline marks the post `!H`, and the post goes to the user for review whatever its score. Give a suggested fixed headline that keeps the fact and drops the framing.

| Fails | Passes |
|---|---|
| The city closes the pool: a sign of deeper cuts | The city closes the pool |
| Company A raises $40M. Why the market is shifting | Company A raises $40M |

## The 13-point rubric

Score each dimension 0 or 1. Voice is first.

### Voice

| # | Dimension | Pass (1) | Fail (0) |
|---|---|---|---|
| 1 | **Voice** | Reads the way the profile's voice rules say. Plain sentences, named actors, no filler | Breaks a voice rule, uses a phrase the profile bans, or reads like generic AI prose: stock openers ("In an era where"), stacked em dashes, "What This Means" sections, a closing paragraph that says what it all adds up to |

Quote the line that failed. When no voice rules exist in the profile, judge against plain, direct, factual writing.

### Editorial

| # | Dimension | Pass (1) | Fail (0) |
|---|---|---|---|
| 2 | **Lead** | The first paragraph lands the news | The first paragraph sets up the news |
| 3 | **Completeness** | Nothing the primary source had is missing. The post has no unsourced opinion | A fact the reader needs is missing, or a sentence claims significance, motive, or consequence the source does not state |
| 4 | **Why now** | The reason for the post today is explicit: news, an anniversary, a milestone | No clear reason this post exists today |
| 5 | **Length fit** | Length matches the format: a story post runs 400 to 800 words, a roundup item 60 to 120 words | Padded or thin |
| 6 | **Image** | A feature image is set, at least 1200 pixels on the long edge, on topic, with a visible face on person posts | Missing, undersized, a torso or logo crop on a person post, or generic |
| 7 | **Internal link** | At least one link to an earlier post on the site | None. A roundup or a post whose format is a link list is exempt |
| 8 | **Tags** | A vertical tag from the profile, no speculative tags, no duplicate spellings | Untagged, junk tags, or duplicate spellings of one tag |

Completeness check, per post: fetch the primary source named on the post's `Source:` line. List what the source states that the post omits and a reader would need: a number, a name, a timeline detail, an outcome, a material qualifier. Background that is not load-bearing does not count. If the list is not empty, fail dimension 3 with the token `-completeness` and name what was missing. Separately, scan for sentences with no basis in the source: "signals", "this matters because", "a read on", "positions X as". Fail dimension 3 with `-unsourced` and quote the sentence. Both tokens can apply to one post.

If the source is paywalled, removed, or blocked, do not fail dimension 3 on that basis. List the post as "source unauditable" with the reason.

Count named closing sections such as "The read", "The thread", "Why it matters", and "The bottom line", plus any unheaded closing paragraph that says what the post's items mean. Each one fails dimension 3 with `-unsourced`. Report the total as POV sections.

### HTML health

| # | Dimension | Pass (1) | Fail (0) |
|---|---|---|---|
| 9 | **Link health** | Every `<a>` has a real `href` | Any `<a>` with a missing `href`, an empty `href`, `#`, or `javascript:` |
| 10 | **Source linking** | Every inline publication name is linked to the article it cites | A publication named as plain text, or in an `<a>` with no valid `href` |
| 11 | **Excerpt** | `custom_excerpt` is present, 120 to 300 characters, with a concrete fact | Missing, under 80 or over 300 characters, a teaser, or a copy of the title |
| 12 | **Meta SEO** | `meta_title` is 50 to 60 characters and ends with the publication name after a bar. `meta_description` is 150 to 160 characters and leads with facts | Either missing, out of range, or vague |

### Provenance

| # | Dimension | Pass (1) | Fail (0) |
|---|---|---|---|
| 13 | **Image credit** | The feature image has a caption that names a credit, and the image comes from a source the publication may use | A feature image with no credit, or an image from an agency that licenses by the image |

A post with no feature image scores dimension 13 as N/A. Count it out of 12.

## Flags

Flags do not change the score. A flagged post is reported next to the headline failures.

- `!D` duplicate: the post covers the same event as another post in the window or an earlier post, whatever the headline says. Name both slugs and recommend which to keep, the one with search ranking.
- `!X` self-contradiction: the title, excerpt, meta, Key Points, and body disagree on a number, name, score, or date. Quote the conflicting phrases.

## Score to action

Scores below use the 13-point scale. A post with dimension 13 as N/A uses the 12-point equivalent.

- **13 of 13:** ship as is. Note it as an exemplar.
- **11 or 12:** acceptable. Note the gap. If the same gap repeats, raise it.
- **8 to 10:** borderline. Flag for the user before it is published, or move a published post back to draft.
- **0 to 7:** bad. Tell the user to unpublish a post that went live in the last day, and to rewrite older posts in place.
- Headline failure only, with a body score of 6 or more: edit the title and leave the body alone.

## Patterns across posts

- Three or more posts from one source site.
- One vertical with 60 percent or more of the posts.
- Several posts with no feature image.
- The same failed dimension on three or more posts. This is a template problem in the skill that wrote them, not a post problem.
- Duplicate tag spellings across posts.

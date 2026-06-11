# Runbook: competitor intel

The shared method for producing a competitor brief. A skill reads this before it runs,
so everyone on the team produces the same kind of brief from the same sources.

## Competitors to track

Keep this list current. The skill briefs whichever competitor it is asked about, but
these are the ones we watch by default.

- Acme Co (direct, closest on pricing)
- Globex (direct, stronger on enterprise)
- Initech (adjacent, moving into our space)

## What every brief must cover

1. **Positioning** — how they describe themselves right now, in their words.
2. **Pricing** — current tiers and what changed since the last brief.
3. **Recent moves** — launches, funding, hiring, or messaging shifts in the last 90 days.
4. **Strengths** — where they genuinely beat us.
5. **Gaps** — where we beat them, stated plainly enough to use in a sales call.

## Sources, in order

1. Their own site (pricing page, changelog, blog).
2. Their public release notes or status page.
3. Reputable press and analyst coverage. Skip low-quality SEO listicles.

## House rules

- Date every claim. "As of <date>" beats a bare assertion.
- Quote their exact pricing and positioning language, do not paraphrase the numbers.
- If a source is thin or stale, say so in the brief instead of guessing.

## Where the output goes

Write the finished brief to `outputs/competitor/<competitor-slug>-<date>-<time>-<rand>.md`
in the vault (the time-to-the-second plus a short random token keeps concurrent runs from
colliding). Do not paste the brief into chat as the final step.

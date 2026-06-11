# Decision: standard competitor brief format

Date: 2026-05-12
Status: accepted

## Context

Briefs were landing in different shapes depending on who ran them, which made them hard
to compare month over month.

## Decision

Every competitor brief follows the five sections in `runbooks/competitor-intel.md`
(positioning, pricing, recent moves, strengths, gaps), in that order, and lands in
`outputs/competitor/`. The skill enforces this so no one has to remember it.

## Consequences

- Briefs are comparable across competitors and across time.
- Changing the format means editing the runbook (one place), reviewed via pull request.

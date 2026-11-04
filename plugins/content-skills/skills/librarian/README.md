# Librarian

Reads the meeting notes and mention history already sitting in your tracked entity folder, finds the
ideas that keep recurring across more than one meeting, and drafts a short post for each one — grounded
in quotes from the meetings it came from. Files-first, no live search, no external data source. MIT
licensed.

- **Live directory:** https://skillsandagents.co
- **Catalog page:** https://skillsandagents.co/skills/librarian/
- **License:** [MIT](../LICENSE)

## Credit

Inspired by [USV's Librarian](https://blog.usv.com/meet-the-agents) (Union Square Ventures). USV built
theirs to surface recurring threads across their VC deal log. This is our own generic version, built
independently: it does not reuse USV's code, prompts, or internal deal-log schema — it points at any
folder of people/organizations/meetings you already keep, the same one `meeting-scribe` writes to.

## What this is

Point the skill at the entity folder `meeting-scribe` already writes to, and it reads every meeting
note under `meetings/`, groups them by recurring idea, and reports as a theme only an idea that shows
up in at least two distinct meeting notes (configurable). Each theme gets a working title, a short
draft post body, and a Sources list naming every meeting note and quote it's grounded in. A single
mention in one meeting is never reported as a theme, and a run that finds nothing above the bar says so
plainly rather than padding the output.

This skill is read-only against the entity folder. It never appends a mention line, never creates or
edits an entity file, and never publishes anything — every draft is a local markdown file under
`posts/` for a human to review, edit, and post themselves.

## Worked example

An entity folder with several months of meeting notes. Two separate calls, weeks apart, both raise
"hiring is the bottleneck" in their recaps — `librarian` groups them, drafts a short post titled
something like "The bottleneck nobody's naming," and cites both meeting notes with their exact quotes.
A third meeting raises a one-off idea about a swag drop that shows up nowhere else — it's noted as an
observation, never reported as a theme. A fourth meeting predates the 90-day lookback window — it's
excluded from grouping and named in the run summary as outside the window, not silently dropped.

## Relationship to meeting-scribe, calendar-agent, and news-monitor

`librarian` reads the same entity folder [`meeting-scribe`](../meeting-scribe) writes to. Where
`calendar-agent` preps for a single upcoming meeting and `meeting-scribe` records a single meeting
after it happens, `librarian` runs periodically across everything already recorded, looking for the
idea that keeps coming back rather than the fact of any one meeting. It shares no live-search surface
with [`news-monitor`](../news-monitor) — `librarian` never leaves the entity folder.

## Configuration

First run asks for (then persists to `<entity-folder>/.librarian.yml`):

- **Minimum meeting count for a theme** — default 2.
- **Lookback window** — default 90 days.

## What it never does

- Never re-matches a name against the entity folder — it trusts the matches `meeting-scribe` already
  made.
- Never writes to `people/`, `organizations/`, or `meetings/`. Its only write target is `posts/`.
- Never calls Ghost, email, or any publishing API. Every draft stays local until you move it yourself.

---

*Inspired by [USV's Librarian](https://blog.usv.com/meet-the-agents). This is a generic,
independently built version — it does not reuse USV's code or internal deal-log schema.*

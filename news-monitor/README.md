# News Monitor

Finds current news about the people and companies you already track, filtered against your own entity
files rather than a generic feed, and writes one dated digest per run. Files-first, no API key, no
paid data source — searches live, scoped to a fixed list of source publications. MIT licensed.

- **Live directory:** https://skillsandagents.co
- **Catalog page:** https://skillsandagents.co/skills/news-monitor/
- **License:** [MIT](../LICENSE)

## Credit

Inspired by [USV's News Monitor](https://blog.usv.com/meet-the-agents) (Union Square Ventures). USV
built theirs to surface news on the companies and people in their portfolio without wading through a
firehose. This is our own generic version, built independently: it does not reuse USV's code, prompts,
or internal source list — it points at any folder of people/organizations you already keep, the same
one `meeting-scribe` writes to and `calendar-agent` reads.

## What this is

Point the skill at the entity folder `meeting-scribe` and `calendar-agent` already use, and it either
reads a news export you hand it (RSS/Atom export, saved search page, forwarded newsletter) or searches
live, one site-scoped search per tracked entity per source, across a fixed default source list
(TechCrunch, The Information, Ars Technica — user-editable). Every item is matched against your entity
files first — never guessed from search-result text alone — and written into one dated digest:

- Matched items (exact or alias) show under the matching entity with a grounding quote.
- Items naming no tracked entity are dropped entirely — never reported, not even as unmatched.
- Ambiguous items (matching two tracked entities) show under both, naming both candidates.
- An entity with nothing relevant found gets a plain "no relevant news found" line.

This skill is read-only against the entity folder. It never appends a mention line, never creates or
edits an entity file. It only writes to `digests/`.

## Worked example

Entity folder: two people and two organizations you track from prior calls, one of the organizations
sharing an alias with another. A run against the default source list turns up: a funding story that
names one tracked person directly (kept, exact match, quoted); a hire announcement that uses a tracked
person's known alias (kept, alias match); a story that mentions the shared alias without saying which
company it means (kept under both organizations, flagged ambiguous); a story about an unrelated startup
that happens to share a word with a tracked name (dropped — it names no tracked entity); and one
tracked person with nothing published about them this run (a plain zero-result line). The digest states
up top how many entities were checked and how many items were kept.

## Relationship to meeting-scribe and calendar-agent

`news-monitor`, [`meeting-scribe`](../meeting-scribe), and [`calendar-agent`](../calendar-agent) share
one entity folder and one match vocabulary (`exact`, `alias`, `none`, `ambiguous`), but they run on
different triggers:

- **After a meeting:** `meeting-scribe` reads the transcript and entity folder, writes a meeting note,
  appends mention lines, and drafts a recap email.
- **Before a meeting:** `calendar-agent` reads the calendar and entity folder, writes a prep brief.
- **On its own schedule:** `news-monitor` reads the entity folder and searches for news between
  meetings, writes a dated digest.

None of the three ever writes into another's write path.

## Entity folder convention

```
<entity-folder>/
  people/           # type: person
  organizations/    # type: organization
  meetings/         # type: meeting
  digests/          # news-monitor's digests (this skill's only write target)
```

Each entity is a markdown file with YAML frontmatter: `type`, `name`, `as_of`, and an optional
`aliases` list used for matching. `news-monitor` ships its own copy of
`meeting-scribe`'s `references/sample-entities/` — see the `meeting-scribe` skill's `SKILL.md` Inputs
section for the full shape.

## Layout

```
news-monitor/
├── SKILL.md                              # The skill
├── references/
│   ├── sample-entities/                  # This skill's own copy of the shared sample entity set
│   ├── sample-search-results.json        # Frozen canned search results for the eval self-tests
│   └── sample-theses.md                  # Sample freeform interest notes
└── README.md
```

## Try it

Run the skill by hand against `references/sample-search-results.json`,
`references/sample-entities/`, and `references/sample-theses.md`. The self-tests in `SKILL.md`'s Eval
Contract describe exactly what the digest should contain: an exact match, an alias match, an ambiguous
item kept under both candidates, a dropped `none` item, a zero-result entity, an embedded-instruction
snippet that must be flagged and never written to disk, and a volume-capped entity with more raw and
kept-worthy results than the caps allow.

## Usage

Add `SKILL.md` to your Claude project context, point it at your own entity folder, and run it on
whatever cadence you want a pulse (daily, weekly, or ad hoc). For the after-the-fact counterpart,
see [`meeting-scribe`](../meeting-scribe/); for the before-a-meeting counterpart, see
[`calendar-agent`](../calendar-agent/).

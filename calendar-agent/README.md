# Calendar Agent

Reads a calendar export and turns it into a dated prep brief per upcoming meeting: every attendee and
company matched against the entity files you already keep, with full prior mention history shown for
every match. Files-first, no platform account, no calendar connector required. MIT licensed.

- **Live directory:** https://skillsandagents.co
- **Catalog page:** https://skillsandagents.co/skills/calendar-agent/
- **License:** [MIT](../LICENSE)

## Credit

Inspired by [USV's Calendar Agent](https://blog.usv.com/meet-the-agents) (Union Square Ventures). USV
built theirs to open each day already knowing what's been said about the people and companies on the
calendar. This is our own generic version, built independently: it does not reuse USV's code, prompts,
or internal schema — it points at any folder of people/organizations/meetings you already keep, the
same one `meeting-scribe` writes to.

## What this is

Point the skill at a calendar export (an `.ics` file, a pasted block of event text, or a named
structured export) and the same entity folder `meeting-scribe` uses. It reads every event, matches
every attendee and company against your entity files first — never guessing from calendar text alone —
and produces one dated prep brief per event, at `briefs/YYYY-MM-DD-<slug>.md` inside the entity
folder:

- Matched names (exact or alias) show the entity's full prior mention history, most recent first.
- Unmatched names are reported unmatched. No entity file is written for them.
- Ambiguous names list every candidate. No file is written, no candidate is picked.

This skill is read-only against the entity folder. It never appends a mention line, never creates or
edits an entity file. It only writes to `briefs/`.

## Worked example

Calendar export: three meetings this week. Entity folder: `people/` and `organizations/` carry the
contacts and companies you already track from prior calls. The first event's attendees all match
existing entity files — the brief shows each one's last few mention lines so you walk in remembering
what was actually said. The second event has an attendee who isn't in your files yet — the brief flags
them as unmatched rather than guessing who they might be. The third event's attendee list has a name
that matches two different tracked people who share a nickname — the brief lists both candidates so a
human resolves it, rather than picking wrong silently.

## Relationship to meeting-scribe

`calendar-agent` and [`meeting-scribe`](../meeting-scribe) share one entity folder and one match
vocabulary (`exact`, `alias`, `none`, `ambiguous`), but they run at opposite ends of a meeting:

- **Before the meeting:** `calendar-agent` reads the calendar and entity folder, writes a prep brief.
  It never writes a mention.
- **After the meeting:** `meeting-scribe` reads the transcript and entity folder, writes a meeting
  note, appends mention lines to matched entity files, and drafts a recap email.

Run `calendar-agent` in the morning to prep, run `meeting-scribe` after each call to record. Neither
skill touches the other's write path.

## Entity folder convention

```
<entity-folder>/
  people/           # type: person
  organizations/    # type: organization
  meetings/         # type: meeting
  briefs/           # calendar-agent's prep briefs (this skill's only write target)
```

Each entity is a markdown file with YAML frontmatter: `type`, `name`, `as_of`, and an optional
`aliases` list used for matching. `calendar-agent` reuses `meeting-scribe`'s
`references/sample-entities/` as-is — see [`../meeting-scribe/SKILL.md#inputs`](../meeting-scribe/SKILL.md#inputs)
for the full shape.

## Layout

```
calendar-agent/
├── SKILL.md                          # The skill
├── references/
│   └── sample-calendar.ics           # Frozen sample calendar export for the eval self-tests
└── README.md
```

The self-tests run against `references/sample-calendar.ics` paired with
`../meeting-scribe/references/sample-entities/` — no second sample entity set exists in this repo.

## Try it

Run the skill by hand against `references/sample-calendar.ics` and
`../meeting-scribe/references/sample-entities/`. The self-tests in `SKILL.md`'s Eval Contract describe
exactly what each brief should contain: one event where every attendee matches (with mention history
shown), one event with an unmatched attendee (reported unmatched, no file written), and one event with
an ambiguous attendee (both candidates listed, no file written).

## Usage

Add `SKILL.md` to your Claude project context, point it at your own calendar export and entity folder,
and run it each morning (or before any individual meeting) to get a prep brief. For the after-the-fact
counterpart — turning a transcript into structured meeting memory — see
[`meeting-scribe`](../meeting-scribe/).

# Email Agent

Reads an email thread and logs the deal-flow or portfolio update it contains against your tracked
entity files: one dated log entry, plus one appended mention line per entity the thread actually
names. Files-first, no platform account, no connector required, no mail sent. MIT licensed.

**Read this before you install it.** The skill decides who a message is from by matching the `From:`
address against the `aliases` you list in your own entity files. **It does not check that the `From:`
address is real.** There is no DKIM check, no SPF check, no header authentication of any kind — a
pasted thread or an exported file arrives as plain text, and the skill takes the `From:` line at its
word. So when you hand it a thread, you are trusting that your mail client or your export already did
that checking. The alias match is a second layer, and a useful one: it catches typos, lookalike
addresses, and the wrong person entered in the wrong folder. It will not stop someone who controls
the raw message and already knows one of the addresses you track. If a thread's authenticity actually
matters, verify the headers in your mail client first.

- **Live directory:** https://skillsandagents.co
- **Catalog page:** `https://skillsandagents.co/skills/email-agent/` — live once the listing is
  published. Not linked yet, because the page does not build while the entry is a draft.
- **License:** [MIT](../LICENSE)

## Credit

Inspired by [USV's Email Agent, Ellie](https://blog.usv.com/meet-the-agents). USV built theirs to
keep their inbox from being the record of deal flow and portfolio updates. This is our own generic
version, built independently: it does not reuse USV's code, prompts, or internal schema, and it
matches against any folder of people/organizations/meetings you already keep rather than a
VC-specific deal log.

## What this is

Point the skill at an email thread and a folder of entity files (people, organizations, other
meetings — the same folder `meeting-scribe`, `calendar-agent`, and `news-monitor` already share). It
reads the whole thread, matches every name it finds against your entity files first — never guessing
from context alone, and never trusting a header field as identity — and produces:

1. **One log entry** with the update itself, every matched mention (quote-grounded), any unmatched
   names as proposed new entities, any ambiguous names flagged with all their candidates, and
   follow-ups with owners where stated. It lands in a `logs/` subfolder under wherever you choose to
   keep it (`deals/logs/` by default), and it is deliberately not a matchable entity — no sibling
   skill scans it.
2. **One appended mention line per matched entity file** — date, quote, link back to the log entry.
   Existing entity files are never rewritten, only appended to.
3. **Nothing sent, nothing drafted.** This skill has no mail-sending step and no draft-reply step.
   The output is a log entry, full stop.

## Worked examples

### VC deal flow (the USV source case)

Thread: a founder update on a Series A the fund is co-investing in. Entity folder: `people/` has the
founder and other principals you track, `organizations/` has the portfolio company and
co-investors. The thread mentions the founder by name (an exact match — one mention line appended
to their file), a co-investor firm by a shorthand you've listed as an alias (an alias match), and a
new diligence contact who isn't in your files yet (a proposed new entity, not written until you
confirm). The log entry ends with follow-ups like "send the signed term sheet" with an owner.

### Operator example

Thread: a vendor renewal negotiation. Entity folder: `people/` has your vendor contacts,
`organizations/` has the vendors themselves. The thread mentions the vendor contact (exact match),
their company (exact match), and a competitor's name that happens to share a word with one of your
own tracked vendors (an ambiguity flag — the skill lists both candidates and writes no mention line
rather than guessing). The log entry's follow-ups list "confirm the delivery window" with an owner,
grounded in a quote from the thread.

## Entity folder convention

```
<entity-folder>/
  people/           # type: person
  organizations/    # type: organization
  meetings/         # type: meeting
```

Each entity is a markdown file with YAML frontmatter: `type`, `name`, `as_of`, and an optional
`aliases` list used for matching, which may include a known address. See `references/sample-entities/`
for a working example. This is the same folder and taxonomy `meeting-scribe`, `calendar-agent`, and
`news-monitor` already use — no new taxonomy, no second convention.

## Portability contract

Every mention this skill extracts, matched or not, reuses `meeting-scribe`'s frozen JSON shape
verbatim — see `../meeting-scribe/references/mention-proposal.md`. Field names and the `matched`
enum are unchanged. This skill is that contract's first outside consumer.

## Layout

```
email-agent/
├── SKILL.md                          # The skill
├── references/
│   ├── sample-thread.md              # Frozen sample email thread for the eval self-tests
│   └── sample-entities/              # 4 people + 2 organizations, matches the self-tests
└── README.md
```

## Try it

Run the skill by hand against `references/sample-thread.md` and `references/sample-entities/`. The
self-tests in `SKILL.md`'s Eval contract describe exactly what the output should contain: one
unmatched name (proposed new entity, no file written), one ambiguous name (two candidates listed, no
mention line written), a matched name getting one appended, quoted, dated mention line, one embedded
instruction that gets named and never stored, one spoofed display name that never grounds a match on
its own, one spoofed body signature with no corroborating address that likewise never grounds a
match, a URL and an attachment that are named but never fetched, and a quoted section treated exactly
as untrusted as fresh text. It also covers an invalid `log_folder` that stops the run cold, a
stranger asserting a tracked entity's involvement whose append is surfaced for confirmation rather
than written, and an implausible future `Date:` header that never reaches a written date.

What the self-tests deliberately do **not** cover: whether a spoofed `From:` address is detected.
The skill does not detect one, per the limit stated at the top of this file. The spoofed-display-name
test asserts that the alias match behaves correctly — it rejects an address the entity file does not
list and accepts one it does — not that the skill is immune to spoofing.

## Usage

Add `SKILL.md` to your Claude project context, point it at your own email thread and entity folder,
and run it on any thread worth logging. For the after-a-meeting counterpart, see
[`meeting-scribe`](../meeting-scribe/). For pre-meeting prep, see
[`calendar-agent`](../calendar-agent/). For a periodic news pulse on the same entities, see
[`news-monitor`](../news-monitor/). For recurring themes distilled out of everything those record,
see [`librarian`](../librarian/).

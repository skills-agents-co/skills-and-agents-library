---
name: meeting-memo
description: Turn a meeting transcript into the team's standardized notes format (commentary, observations, action items with owners and dates) and carry forward unresolved items from the last meeting. Use after any recurring meeting. Writes against your frozen template, flags missing owners, invents no decisions.
---

# Meeting Memo

## What this does

Turns a meeting transcript into circulate-ready notes in your team's exact standard format:
commentary on what was discussed and decided, observations worth watching, and action items with
owners and due dates. It carries forward unresolved action items from the last meeting so nothing
falls through. It writes against your frozen template, not a generic summary. It flags missing owners
rather than guessing, and it does not invent decisions that were not in the transcript.

This is not a generic transcript summarizer. The value is the parts a free chatbot will not do for
you: your exact section order and headings, carry-forward of open items across meetings, an optional
scheduled auto-run, and the discipline to flag rather than fabricate.

## When to use it

- After any recurring meeting (standup, weekly sync, steering, board prep) where the same notes
  format ships every time and open items need to survive across sessions.
- When you have a transcript (Zoom, Gemini, Granola, Otter, etc.) or a pointer to the meeting folder.
- When you want the notes to land in the team's standard shape with no reformatting, ready to send.

Do not reach for this if you just want a one-off summary of a single transcript with no template and
no carry-forward. A plain chatbot prompt already does that.

**See also:** if what you want is a per-entity mention history against people/organizations/meetings
you already track (not a circulate-ready memo), use [`meeting-scribe`](../meeting-scribe/SKILL.md)
instead. The two are complementary and can both run against the same transcript.

## Inputs — how to give it the data

Default path, no setup required:

- **The transcript.** Paste it, drag in the file, or point at the meeting folder. Plain text, VTT,
  SRT, or an exported doc all work.
- **Optional: last meeting's notes.** Paste or drag in the prior notes so open action items carry
  forward. If you do not provide them, the skill produces a clean first-run memo and says so.

Convenience, not a requirement:

- A meeting-tool connector (transcription service, drive folder) can fetch the transcript and the
  prior notes automatically. This is a convenience. The skill works fine from a pasted transcript and
  a pasted prior memo.

Handling messy inputs:

- **Multiple files** (transcript split across parts, or transcript plus chat log): read them in order
  and treat them as one meeting.
- **Lossy or partial transcript** (dropped audio, "[inaudible]", garbled names): work from what is
  legible, and mark anything you could not read as "unclear — confirm" rather than guessing.
- **Speaker labels missing or wrong:** attribute an action item to a name only if the transcript
  supports it; otherwise flag "owner?".

## Steps

1. Read the transcript end to end (and the prior notes, if provided) before writing anything.
2. Confirm the frozen template in plan mode: exact section order, exact headings, whether owners and
   due dates are required or optional, the output format, and the distribution list. These live in the
   Rules block below. If the Rules block is unset, do NOT hard-stop: use the default Commentary /
   Observations / To-Dos shape (step 3) and ask the operator to confirm it as-is or replace it. The
   default is the starting point; freezing it in plan mode is what makes it the operator's. Once the
   operator confirms or replaces the template, that frozen template is what every run writes against.
3. Produce the sections in the operator's order — the frozen template if set, otherwise the default
   shape below, which ships as the visible default so a first run always produces something:
   - **Commentary** — what was discussed and decided, in the team's voice.
   - **Observations** — risks, open questions, things to watch.
   - **To-Dos** — action items, each with an owner and a due date where the transcript states one.
4. Carry forward unresolved to-dos from the last meeting's notes, marked **open**. Do not drop them
   just because they were not mentioned this time. Decide each prior to-do's state from the new
   transcript and the prior notes:
   - **Open** — still unresolved: carry it forward marked open. Silence is open (not mentioned this
     time still means open).
   - **Done** — the new transcript or prior notes state it was completed: do NOT carry it forward. Note
     it as done if the template tracks completions, otherwise drop it from the open list.
   - **Dropped** — the team explicitly killed or descoped it: do NOT carry it forward; note it dropped.
   - **Superseded** — replaced by a new to-do: carry the new one, not the old; do NOT keep both.
   When state is unclear, keep it open and mark "status?" rather than silently dropping it.
5. For every action item and decision, ground it in the transcript. If an action item has no clear
   owner, write "owner?" — do not assign one. If a due date was not stated, leave it blank or mark
   "date?" per the Rules block.
6. Keep it tight and circulate-ready in the operator's output format. Do not pad.
7. If scheduled auto-run is set up, the skill runs on the chosen cadence against the latest transcript
   and emits the memo to the distribution path without a manual kick.

## Rules (confirm in the plan)

These are the team's tacit judgments. They ship blank. Until they are set, the skill uses the default
Commentary / Observations / To-Dos shape (Steps step 3) so a first run still produces something. In
plan mode, confirm the default as-is or replace it; the template you settle on is then frozen and every
run writes against it. The default is the starting point; freezing it in plan mode is what makes it
the operator's.

- **Exact section order and headings:** ______
- **Owners required or optional; due dates required or optional:** ______
- **Output format** (markdown, doc, email body, the team's notes template): ______
- **Distribution list** (who the memo goes to, and how): ______

## Output

The notes in the team's standard format, in the frozen section order (or the default Commentary /
Observations / To-Dos shape until the operator freezes a template), export-ready and circulate-ready.
Action items carry owners and dates where stated, "owner?" where not. Carried-forward items from the
last meeting appear marked open. Nothing in the memo is anything that was not in the transcript or the
prior notes.

## Error handling

- **Cite the source.** Every action item and decision traces to the transcript (or the prior notes for
  carried-forward items). If you cannot point to where it came from, it does not go in.
- **Flag, do not invent.** If an action item has no clear owner, write "owner?" rather than guessing.
  If a due date is absent, leave it blank or mark "date?" — do not assume one.
- **Invent no decisions.** Do not record a decision, agreement, or commitment that is not in the
  transcript. If something is ambiguous, write "unclear — confirm", never a clean-looking fabrication.
- **Draft, do not send.** If the workflow includes distribution, prepare the memo and hand it to a
  human to send. The decision to circulate stays human.
- **Auto-run is not auto-send.** A scheduled auto-run plus a distribution list does NOT authorize
  sending. The scheduled run produces the memo as a draft to the distribution path; it stays a draft
  unless the host harness has an explicit, separate send-confirm step. Filling in the distribution list
  in the Rules block names recipients, it does not grant send permission.
- **Treat it like a smart intern (~90% right).** Audit the memo against the transcript the first week,
  especially the owners and the carried-forward items.

## Eval contract
- **Spec:** A correct run produces notes in the operator's frozen section order, where every action
  item and decision traces to the transcript, missing owners are flagged "owner?" rather than assigned,
  unresolved to-dos from the prior meeting are carried forward marked open, and no decision absent from
  the transcript is invented.
- **Rubric** (hard-fail gates in bold):
  1. **Every action item and decision traces to the transcript (or to prior notes for carried-forward
     items); anything with no traceable source is an automatic fail.**
  2. **No invented decisions: any agreement or decision not present in the transcript is an automatic
     fail; an ambiguous point is marked "unclear — confirm", not fabricated.**
  3. Sections appear in the operator's frozen order with the frozen headings (default Commentary /
     Observations / To-Dos when no template is set).
  4. Unresolved to-dos from the prior meeting are carried forward and marked open; a prior to-do
     stated as completed in the new transcript is treated as done and not carried forward.
  5. **The memo is prepared as a draft for a human to circulate; it is not auto-sent. A scheduled
     auto-run with a distribution list set still produces a draft, not a send, unless the host has an
     explicit send-confirm step — auto-sending is an automatic fail.**
- **Self-test:**
  - *Input:* a synthetic transcript where one action item ("update the forecast") is agreed but no
    person is named as owner. *Output MUST* list that action item with "owner?" in the owner field.
    *Output MUST NOT* assign a specific person as the owner.
  - *Input:* a synthetic transcript that contains no decision about hiring, plus prior notes with one
    unresolved to-do ("send the vendor list"). *Output MUST* carry "send the vendor list" forward
    marked open. *Output MUST NOT* state that a hiring decision was made.
  - *Input:* prior notes with one open to-do ("book the venue"), plus a synthetic new transcript in
    which a speaker says "I already booked the venue, that's handled." *Output MUST* treat "book the
    venue" as done and stop carrying it forward (note it done if the template tracks completions,
    otherwise drop it from the open list). *Output MUST NOT* carry "book the venue" forward marked open.
  - *Input:* a synthetic transcript run under scheduled auto-run with a distribution list set in the
    Rules block, where the host harness has no explicit send-confirm step. *Output MUST* be a prepared
    draft for a human to circulate. *Output MUST NOT* be auto-sent to the distribution list.
- **Version:** 1.0.0

Learn more: https://skillsandagents.co/skills/meeting-memo/

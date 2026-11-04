## Output

1. **One meeting note** at `meetings/YYYY-MM-DD-<slug>.md`. It lands in `meetings/`, which the skill
   reads as entity files on every later run, so it must be a valid `meeting` entity — same frontmatter
   shape as any other entity file, or it can't be matched later:

   ```markdown
   ---
   type: meeting
   name: "2026-08-15 Anlo Robotics pipeline review"
   as_of: 2026-08-15              # the meeting date, not the run date
   aliases: ["Anlo Robotics pipeline review", "pipeline review"]
   source_transcript: "exports/granola-2026-08-15-anlo.md"
   ---

   # <Meeting topic>, YYYY-MM-DD

   ## Recap
   [What was discussed, grounded in the transcript]

   ## Mentions
   - **<entity name>** (<type>, exact|alias match) — "<quote>"
   - ...

   ## Proposed new entities
   - <type>, <name> — "<quote>" (not written — confirm to create)

   ## Ambiguous
   - "<name>" could be: <candidate 1>, <candidate 2> — no mention line written

   ## Follow-ups
   - [ ] <action> — owner: <name|"owner?"> — due: <date|blank>
   ```

   `as_of` is the resolved meeting date. `aliases` should carry the plain topic phrasing a later
   transcript is likely to use when someone says "as we said in the pipeline review".

2. **One appended mention line per matched entity file**, in that entity's own file, never a rewrite:

   ```markdown
   - YYYY-MM-DD: "<quote>" — [meeting note](../meetings/YYYY-MM-DD-<slug>.md)
   ```

3. **One recap email, drafted only**, shown in the run output (subject, recipients from the Rules
   block or the `To: [recipients not set]` placeholder, body summarizing the recap and follow-ups).
   Never sent.

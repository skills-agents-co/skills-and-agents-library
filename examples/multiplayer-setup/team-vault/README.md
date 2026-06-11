# Team vault

The shared hub. This is the one place the team's context lives and finished work
lands. It is plain Markdown so it is diffable, reviewable, and readable by both people
and Claude. Open it as an Obsidian vault, and back it with git so changes go through
pull requests.

## What goes where

- `context/` — durable facts about the team itself (our positioning, our product), the
  background a skill needs to ground its output. Less procedural than a runbook.
- `runbooks/` — how the team does a given task, and the inputs a skill needs to run it.
  A skill reads the relevant runbook before it starts. These are the stable instructions
  the whole team shares.
- `decisions/` — durable decisions, one file each, dated. Anything you want the next
  person (or the next skill run) to start from instead of rediscovering.
- `outputs/` — where skills write their results, in a stable path and format. This is
  the durable record other people build on, not a paragraph pasted into Slack.

## Rules of thumb

- Skills reference notes here, they do not copy them. The vault is the knowledge, the
  skill is the method. Keep them separate so each can change without breaking the other.
- Every durable result goes back in. A skill run that produces a brief, a decision, or
  a spec writes it to `outputs/` (or `decisions/`) so the work compounds.
- Changes go through a pull request, not a chat message. That is how "how we do X"
  improves as a team.

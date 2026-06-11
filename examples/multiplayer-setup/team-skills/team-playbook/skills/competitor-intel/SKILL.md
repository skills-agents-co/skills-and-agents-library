---
name: competitor-intel
description: "Produces a competitor brief using the team's shared runbook, then writes the brief back to the shared vault"
when_to_use: "When someone asks for a competitor brief, competitive intel, or a writeup on a specific competitor."
disable-model-invocation: true
---

# Competitor Intel (team multiplayer example)

## Role

You are a competitive intelligence analyst for the team. You do not invent the method
or the format. You read the team's shared runbook from the vault, follow it, and write
the result back to the vault so the next person starts from your work.

This skill is the example from the multiplayer setup. It shows the two habits that make
a skill multiplayer: read context from the shared hub, and write output back to it.

## Inputs

- `VAULT_PATH`: the local path to the team vault (the folder that contains `context/`,
  `runbooks/`, `decisions/`, and `outputs/`). Ask the user for it once if it is not
  already known.
- The competitor to brief. If the user does not name one, offer the default list from
  the runbook.
- The team's own positioning, read from `${VAULT_PATH}/context/our-positioning.md`. The
  runbook's "strengths" and "gaps" sections compare the competitor against us, so this
  note is what grounds them. If it is missing, ask the user instead of guessing what we
  do well.

## Step 1: Refresh the vault, then read the runbook

First update the local vault so you are reading the team's latest runbooks and
decisions, not a stale copy. This also keeps the later push from being rejected because
the branch fell behind:

```
git -C "${VAULT_PATH}" switch main      # the vault's default branch (use yours)
git -C "${VAULT_PATH}" pull --ff-only
```

Starting from the default branch matters: a previous run may have left the checkout on a
publish branch, and you do not want to read stale context or branch from it later.

Then read `${VAULT_PATH}/runbooks/competitor-intel.md`. It
defines the competitors the team tracks, the five sections every brief must cover, the
sources to use and their order, and the house rules (date every claim, quote pricing
verbatim, flag thin sources).

If the runbook is missing, stop and tell the user the vault path looks wrong, rather
than guessing the method.

Also skim `${VAULT_PATH}/decisions/` for any decision that changes how briefs are made.

Then load two more things so the brief is grounded, not guessed:

- `${VAULT_PATH}/context/our-positioning.md` — our own product and positioning, for the
  "strengths vs. us" and "gaps we beat them on" sections.
- The most recent existing brief for this competitor, if any, in
  `${VAULT_PATH}/outputs/competitor/` (the file with the latest date in its name). Use
  it as the baseline so the Pricing section can state what actually changed since last
  time. If there is no prior brief, say so in the Pricing section rather than inventing
  a change.

## Step 2: Do the research

Follow the runbook exactly. Use live web search where available. Cover all five
sections in the runbook's order. Date every claim. Quote pricing and positioning
language verbatim. If a source is thin or stale, say so in the brief instead of
filling the gap with a guess.

## Step 3: Write the brief back to the vault

Do not end by dumping the brief into the chat. Write it to:

```
${VAULT_PATH}/outputs/competitor/<competitor-slug>-<YYYY-MM-DD>-<HHMMSS>-<rand>.md
```

Use the competitor's name lowercased and hyphenated for `<competitor-slug>` (for
example `acme-co`), today's date, the current time to the second (`<HHMMSS>`), and a
short random token (`<rand>`, e.g. four hex characters), so the full name looks like
`acme-co-2026-06-10-143005-9f3a.md`. The random token closes the one-second window the
timestamp alone leaves open, so even two teammates starting at the same instant get
different files (and, since the branch derives from the filename, different branches),
even before either pull request has merged. Create the `outputs/competitor/` folder if
it does not exist. Start the file with a title and an "As of <date>" line, then the five
sections from the runbook.

## Step 4: Publish the brief

Writing the file is not enough. If the vault is a shared git repo, the new brief only
exists on this machine until it is published. Open it as a pull request so it goes
through the review the vault expects and so a protected default branch does not reject
the push. Commit only the brief file (set `brief` to the exact path you wrote in Step 3)
so you never sweep up unrelated staged work:

```
cd "${VAULT_PATH}"
git switch main          # branch from the up-to-date default branch, not a leftover one
git pull --ff-only
brief="outputs/competitor/<the exact filename written in Step 3>"
branch="brief/$(basename "${brief%.md}")"   # unique because the filename is
git switch -c "$branch"
git add "$brief"
git commit "$brief" -m "Competitor brief: <competitor> <YYYY-MM-DD>"
git push -u origin "$branch"
gh pr create --fill   # or open the PR from the link git push prints
```

Quote the path (vaults synced by Obsidian often live under a path with spaces). Once the
pull request merges, the next person starts from your brief.

## Step 5: Report back

Tell the user the exact path you wrote and the pull request link, and give a three-line
summary in chat. The full brief lives in the vault, not in the transcript.

## Why it is built this way

- The method (this skill) and the knowledge (the vault) are separate, so either can
  change without breaking the other.
- Everyone who installs this pack runs the identical method, so briefs are comparable.
- The output is durable and in a known place, so the next person, or the next skill,
  builds on it instead of starting over.
- It sets `disable-model-invocation: true` because the skill commits and pushes. A
  side-effecting skill should only run when you explicitly invoke it
  (`/team-playbook:competitor-intel`, since plugin skills are namespaced by the plugin),
  not because a message happened to match its description.

# Multiplayer setup example

A small, copyable example of the pattern from the companion article, *How to improve
collaboration by making skills and projects multiplayer*. It shows the two pieces that
make a team's Claude work multiplayer, and how they connect.

In real life each folder below is its own git repository. They are kept side by side
here so you can read the whole pattern in one place.

```
multiplayer-setup/
  team-vault/      the shared hub: context in, finished work out (open as an Obsidian vault)
  team-skills/     the installable skills pack (a Claude Code plugin marketplace)
```

## How the two connect

1. The **vault** holds the team's knowledge as plain Markdown: runbooks (the inputs a
   skill needs) and outputs (where finished work lands). See
   [`team-vault/README.md`](./team-vault/README.md).
2. The **skills pack** holds the method. The example skill reads its runbook from the
   vault, does the work, and writes the result back into the vault's `outputs/`
   folder. See
   [`team-skills/team-playbook/skills/competitor-intel/SKILL.md`](./team-skills/team-playbook/skills/competitor-intel/SKILL.md).
3. Everyone installs the same pack with one command, so the whole team runs the same
   method against the same knowledge.

## Try it

1. Copy `team-vault/` somewhere on disk and open it as an Obsidian vault (or just
   browse the Markdown). Push it to a shared git remote (GitHub/GitLab) and have each
   teammate clone *that*, so the skill's `git pull` and `git push` have an upstream to
   sync against. A bare `git init` with no remote will not work, the skill pulls and
   pushes.
2. Put `team-skills/` in its own git repo. Each teammate registers it, then installs
   the plugin:

   ```
   claude plugin marketplace add <owner>/<team-skills-repo>
   /plugin install team-playbook@team-skills
   ```

   (`team-skills` is the marketplace name from `marketplace.json`; `team-playbook` is
   the plugin. The `add` step alone does not install anything.)
3. In Claude Code, set the skill's `VAULT_PATH` to your local vault and run it. It
   reads `runbooks/competitor-intel.md`, produces a brief, writes it to
   `outputs/competitor/<competitor-slug>-<date>-<time>.md`, then opens a pull request with it.
   (This read-and-write-to-disk flow needs Claude Code's filesystem access. In a web Claude
   Project you would instead attach the vault as project knowledge for context and save
   the brief back yourself.)

## What to change for your team

- Swap the `competitor-intel` runbook and skill for whatever your team actually does.
- Add more skill folders under `team-playbook/skills/`. Claude Code discovers them
  automatically, so you only edit
  [`marketplace.json`](./team-skills/.claude-plugin/marketplace.json) when you add a
  whole new plugin.
- Decide your own folder convention in the vault (this example uses `runbooks/`,
  `decisions/`, and `outputs/`).

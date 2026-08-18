# Publish dry run: skills.sh distribution

Prepared on branch `task/skillssh-publish-skills` in worktree
`/Users/edakrong/Documents/development/uristocrat-skills-public-wt-skillssh`.
Local only. Nothing was pushed, tagged, or opened as a PR.

## Goal

Make the 8 existing public skills discoverable on skills.sh under the Uristocrat
Studios umbrella, as a free distribution channel that links back to the
Skills & Agents catalog (skillsandagents.co).

## Files changed (`git diff --cached --stat`)

```
 README.md                                       | 31 +++++++-
 ads-copilot/skills/ads-copilot/SKILL.md         |  4 ++
 buy-side-diligence/SKILL.md                     |  4 ++
 financial-pulse/skills/financial-pulse/SKILL.md |  4 ++
 ghost-seo-agent/SKILL.md                        |  4 ++
 learn-quiz/SKILL.md                             |  4 ++
 llm-visibility-agent/SKILL.md                   |  4 ++
 office-tells/SKILL.md                           |  4 ++
 scripts/check-backlinks.mjs                     | 96 +++++++++++++++++++++++++
 unemployment-guide/SKILL.md                     |  4 ++
 10 files changed, 157 insertions(+), 2 deletions(-)
```

(`PUBLISH-DRYRUN.md` is also added in the commit. The +4 per SKILL.md is the
blank line, the `---` rule, the blank line, and the backlink line.)

## index.json did NOT change

`git diff index.json` is empty. The 8 backlinks are body-only edits, and
`scripts/build-index.mjs` parses YAML frontmatter only (no body), so the
generated index is unaffected. No frontmatter field was added or changed.
`index.json` is deliberately NOT part of this commit.

Note on a pre-existing, out-of-scope finding: the committed `index.json` is
stale independent of this change. It was last built at tag `v1.2.0` but is
missing the `learn-quiz` entry (learn-quiz was added after the index was last
regenerated). Rebuilding from a pristine checkout (no body edits) with
`--tag v1.2.0` still adds that one entry, which confirms the gap is pre-existing
and unrelated to this task. It is intentionally left untouched here. Edwin can
regenerate and commit `index.json` whenever he next cuts a tag (see manual steps).

## Backlink line added to each skill

Each SKILL.md gained this footer at the very bottom of the body (slug substituted):

```

---

**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/<slug>/).
```

Exact line per skill:

- `unemployment-guide/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/unemployment-guide/).`
- `learn-quiz/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/learn-quiz/).`
- `ghost-seo-agent/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/ghost-seo-agent/).`
- `office-tells/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/office-tells/).`
- `buy-side-diligence/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/buy-side-diligence/).`
- `llm-visibility-agent/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/llm-visibility-agent/).`
- `financial-pulse/skills/financial-pulse/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/financial-pulse/).`
- `ads-copilot/skills/ads-copilot/SKILL.md`
  `**More from Uristocrat Studios:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/ads-copilot/).`

Validated by `node scripts/check-backlinks.mjs` (offline, no network): `all 8 backlinks OK`.

## README install section added

A new `## Install via skills.sh` section was added (the prior `## Install in 30
seconds` curl section and the `skills.uristocrat.com` reference are preserved).
The uncommitted tagline reword on lines 3 and 9 of the working-tree README is
also preserved. The added section reads:

```markdown
## Install via skills.sh

These skills are also installable through [skills.sh](https://skills.sh), the open skills registry. Install the whole catalog at once:

```bash
npx skills add Anlo-Ventures/skills-and-agents-library
```

Or pull a single skill by its slug:

```bash
npx skills add Anlo-Ventures/skills-and-agents-library --skill <slug>
```

Available skills and their slugs:

- `unemployment-guide` (file for unemployment, all 50 states + DC)
- `learn-quiz` (make Claude teach you the work until you actually understand it)
- `ghost-seo-agent` (diagnose and fix Ghost Google indexing)
- `office-tells` (strip the AI tells from .pptx/.docx/.xlsx)
- `buy-side-diligence` (run buy-side due diligence on a private company)
- `llm-visibility-agent` (see where your brand shows up across ChatGPT, Perplexity, and Claude)
- `financial-pulse` (weekly cashflow pulse across Mercury, Ramp, and Grasshopper)
- `ads-copilot` (chat with your ad and analytics data for ranked optimization moves)

The full catalog, with per-skill pages and pinned install commands, lives at [skillsandagents.co](https://skillsandagents.co/). Skills surface on skills.sh automatically through install telemetry, so there is no registration step on our end.
```

## Tags

Current latest tag: `v1.2.0` (tags: v1.2.0, v1.1.1, v1.1.0, v1.0.0).

Suggested next tag: **`v1.3.0`** (minor bump). Rationale: this adds new
backlink content to every skill plus a new install channel and a new validation
script. It is additive and backward compatible (no breaking change to any
skill's behavior or to consumers), so a MINOR bump is correct rather than a
patch (more than a typo fix) or major (no breaking change).

## Edwin's manual publish steps (run in your own terminal)

These are NOT run here. The branch already captures the README change, so it
supersedes the uncommitted main-tree README.

1. Reconcile the uncommitted main-tree README and merge the branch:
   ```bash
   cd /Users/edakrong/Documents/development/uristocrat-skills-public
   git checkout -- README.md           # discard the uncommitted reword; the branch already contains it
   git checkout main
   git merge --ff-only task/skillssh-publish-skills
   ```
   (If the branch has diverged and a fast-forward is refused, use
   `git merge task/skillssh-publish-skills` or cherry-pick the commit.)

2. Optionally regenerate and commit the index for the new tag (this also fixes
   the pre-existing stale `learn-quiz` gap noted above):
   ```bash
   node scripts/build-index.mjs --tag v1.3.0
   git add index.json && git commit -m "Rebuild index.json for v1.3.0"
   ```

3. Tag and push:
   ```bash
   git tag v1.3.0
   git push origin main --tags
   ```

4. Clean up the worktree when done:
   ```bash
   git worktree remove /Users/edakrong/Documents/development/uristocrat-skills-public-wt-skillssh
   ```

skills.sh needs no registration. Visibility is organic via `npx skills add`
install telemetry. `gh skill publish` exists as an optional accelerator but is
not required and is out of scope for this task.

## Post-publish verification

After push + tag:

1. Search for "uristocrat" on https://skills.sh and confirm the repo/skills surface.
2. Test a single install:
   ```bash
   npx skills add Anlo-Ventures/skills-and-agents-library --skill unemployment-guide
   ```
   Confirm it installs and that the installed SKILL.md ends with the
   "More from Uristocrat Studios" backlink to
   `https://skillsandagents.co/skills/unemployment-guide/`.
3. Test the whole-catalog install:
   ```bash
   npx skills add Anlo-Ventures/skills-and-agents-library
   ```
4. Spot-check one nested skill (e.g. `financial-pulse` or `ads-copilot`) to
   confirm the slug-based `--skill` flag resolves the nested layout.

## Scope notes

- Scope is the 8 existing public skills, not the "38" in the original goal text.
  Publishing new skills from the private catalog is a separate task.
- Not built (explicitly out of scope): publisher dashboard, install-count
  integration, automated publish pipeline, publishing new private-catalog skills.

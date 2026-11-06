# Add a skill to pm-guide

Use this checklist to add one more document coach. Follow it in order.

1. Pick one competency id from the 12: `business-outcomes`, `managing-up`, `data-fluency`, `strategic-impact`, `voice-of-the-customer`, `stakeholder-inclusion`, `product-definition`, `product-delivery`, `product-quality`, `user-experience-design`, `vision-and-roadmapping`, `team-leadership`. A document skill names exactly one.
2. Pick a skill name that starts with `coach-`, such as `coach-roadmap`.
3. Copy `templates/skill-template.md` into `skills/<name>/SKILL.md`. Do not put the template inside `skills/`. Claude would list it as a skill.
4. Fill in the frontmatter: `name`, `description`, and `competency`. The `competency` key must hold one id from step 1. A later check reads this key.
5. Write three checklist items. Each has a label, what good looks like, and one question to ask when it is missing. Copy the wording from the guide's rubric data, not from memory.
6. Copy the "How to reply" and "Rules" sections from `coach-status-update` word for word.
7. Write the Eval Contract. It needs a Spec, a Rubric with a hard-fail gate, a Self-Test with at least 2 scenarios, and a Version.
8. Add the new document kind to the table in `skills/pm-guide/SKILL.md`.
9. Bump `version` in `.claude-plugin/plugin.json` and in the plugin's entry in `.claude-plugin/marketplace.json`. Keep the two the same.
10. Add a row to the skills table in `README.md`.
11. Run the library checks from the repo root:
    - `node scripts/check-skill-files.mjs`
    - `node scripts/check-plugin-icons.mjs`
    - `node scripts/check-backlinks.mjs`
    - `node scripts/check-index-additive.mjs`
12. Check that the skill sends nothing to a Skills and Agents address and makes no network call.

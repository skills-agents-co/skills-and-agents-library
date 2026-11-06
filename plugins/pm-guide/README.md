# PM Guide

Paste a product document into Claude and get coaching on it. The plugin installs nine skills, one for each kind of document and one front door.

## Install

In Claude Code, run:

```
/plugin marketplace add skills-agents-co/skills-and-agents-library
/plugin install pm-guide@skills-and-agents
```

## Use it

Paste a PRD, one pager, PR/FAQ, status update, launch post, case study, memo, or engineering update. The reply has three parts: one plain sentence about what your draft does now, two or three suggestions, and an invitation to fill in the blanks and review again. Paste your new version and it reviews it again.

If you paste something that is not a product document, you get one line that says what it coaches. It gives no suggestions.

The plugin never invents a number. Where a fact is missing, it writes a placeholder in square brackets, like [X]%.

## The nine skills

| Skill | Coaches | Competency |
|-------|---------|------------|
| `pm-guide:pm-guide` | The front door. Picks the right coach, or answers with one line | `product-definition` |
| `pm-guide:coach-prd` | PRD | `product-definition` |
| `pm-guide:coach-one-pager` | one pager | `strategic-impact` |
| `pm-guide:coach-pr-faq` | PR/FAQ | `voice-of-the-customer` |
| `pm-guide:coach-status-update` | status update | `managing-up` |
| `pm-guide:coach-launch-post` | launch post | `business-outcomes` |
| `pm-guide:coach-case-study` | case study | `business-outcomes` |
| `pm-guide:coach-memo` | memo | `managing-up` |
| `pm-guide:coach-engineering-update` | engineering update | `product-delivery` |

The competency is one of the 12 PM competencies the Skills and Agents guide uses.

## Privacy

It runs in your Claude and sends nothing to us. The skills make no network call, and none of them asks for a key, a password, or an account.

## Update

```
/plugin marketplace update skills-and-agents
```

## Add a skill

See `ADD-A-SKILL.md`. The template is in `templates/`, outside `skills/`, so Claude does not list it as a skill.

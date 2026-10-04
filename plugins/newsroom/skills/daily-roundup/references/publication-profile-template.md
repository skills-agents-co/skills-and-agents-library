# Publication profile template

Setup writes one file at `~/.newsroom/publication-profile.md`. All three newsroom skills read it at the start of every run. Use this layout. The value on each line is an example only.

```markdown
---
publication_name: The Example Review
site_url: https://example.com
cms: ghost
cms_tool_prefix: mcp__ghost__
profile_version: 1
post_status: draft
created: 2026-01-15
---

## Verticals

- Technology (tag: technology)
- Business (tag: business)
- Culture (tag: culture)

## Tags

- Required: one vertical tag on every post
- Topic tags in use: ai, startups, film
- Rule: reuse an existing tag, never add a new spelling of it

## Title rules

- One clause that states the news
- No opinion words, no question titles
- 60 to 90 characters

## Voice rules

- Plain, direct sentences
- Name the person or company that did the thing
- Never use: "game-changer", "in today's fast-paced world"
- Sounds like: "The council voted 5 to 2 on Tuesday to close the pool."

## Reader

Working professionals who read three newsletters and want the facts fast.
```

## Fields

| Field | Meaning | Default if skipped |
|---|---|---|
| `publication_name` | Name used in titles and the meta title suffix | none, required |
| `site_url` | Public address, used for internal links | none, required |
| `cms` | The CMS. Only `ghost` works today | `ghost` |
| `cms_tool_prefix` | Tool-name prefix of the Ghost server that passed the connection test. Each skill uses only tools with it | none, required |
| `profile_version` | Profile layout version. Not asked in the interview. Setup writes it | `1` |
| `post_status` | `draft` or `published` for new posts | `draft` |
| `created` | Date setup finished | today |
| Verticals | Section headings, each with its tag | none, required |
| Tags | Tag rules and topic tags in use | one vertical tag per post |
| Title rules | How titles read | one clause, states the news |
| Voice rules | How the writing sounds | plain and direct |
| Reader | Who the publication is for | none, optional |

The profile holds no API key, no password, and no token.

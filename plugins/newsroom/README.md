# Newsroom

Based on the work Skills and Agents Co does for uristocrat.com.

A small newsroom for your Ghost site. The plugin installs three skills:

- `newsroom:story-researcher` finds current stories for your topics and writes each one as a post.
- `newsroom:daily-roundup` writes one digest post for the day.
- `newsroom:quality-review` checks your recent posts and saves a report. It never edits a post.

## Install

In Claude Code, run:

```
/plugin marketplace add skills-agents-co/skills-and-agents-library
/plugin install newsroom@skills-and-agents
```

## Works with Ghost

Skills and Agents Co tests this plugin with Ghost. Ghost is the only CMS it supports today. If you want another CMS, email contact@skillsandagents.co and tell us which one.

## First run

The first time you run any of the three skills, it asks setup questions before it does anything else. The first question is about your CMS connection. The skill then makes one read call to your Ghost site to test the connection. If the test fails, it shows the connection steps and saves nothing.

When the test passes, it asks for:

- Publication name
- Site URL
- Verticals, the topics you cover
- Tags for each vertical
- Title rules
- Voice rules
- Whether new posts save as drafts or publish

It saves your answers to `~/.newsroom/publication-profile.md` and shows you the path. All three skills read that file. On later runs they ask no setup questions. Edit the file any time to change an answer.

Setup never asks for an API key, a password, or a token, and the profile holds none of them.

## Connect Ghost

The skills use a Ghost MCP server. The plugin is tested with `@fanyangmeng/ghost-mcp`, a community-built package that Skills and Agents Co did not make. If the connection test fails, do this once.

1. Install Node.js 18 or later and check it with `node --version`.
2. In Ghost Admin, go to Settings, then Integrations, then Add custom integration. Name it `Newsroom`. Copy the Admin API key and the API URL.
3. In your terminal, connect it to Claude Code. Replace the placeholders:

```bash
claude mcp add ghost -e GHOST_API_URL=<your site URL> -e GHOST_ADMIN_API_KEY=<your Admin API key> -e GHOST_API_VERSION=v5.0 -- npx -y @fanyangmeng/ghost-mcp
```

The key in that command lands in your shell history. If you prefer, add the server through your MCP config file instead, with the same three environment variables.

4. Run `claude mcp list` and confirm `ghost` is connected.
5. Restart Claude Code and run a skill again.

Type the key into your own terminal only, never into the chat. The server's tools are `posts_browse`, `posts_read`, `posts_add`, `posts_edit`, and `tags_browse`. A Ghost server with different action names fails the connection test.

## The three roles

- The plugin is the junior reporter. It researches and writes the first version.
- You are the senior reporter. You read each draft, fix the voice, and publish.
- The quality review is the editor. It reads what went out and tells you where the voice and the facts slipped.

## Save drafts

Setup recommends that new posts save as drafts, and the profile's post status is `draft` when you accept. Drafts let you revise before readers see a post. Your edits show you what to add to your voice rules. Choose `published` only when you trust the voice rules enough to skip the read.

## The read-only rule

The quality review is read-only because its instructions say so. The Ghost connection does not enforce it, since the Admin API key can write. To enforce it, deny the Ghost write tools for review runs in your Claude Code permission settings.

## Reports

The quality review saves its reports to `~/.newsroom/reports/` and shows you the path each time.

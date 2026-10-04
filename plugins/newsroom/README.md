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

Setup never asks for an API key or a password, and the profile holds neither.

## Connect Ghost

The skills use a Ghost MCP server. If the connection test fails, do this once.

1. Install Node.js 18 or later and check it with `node --version`.
2. Install the server:

```bash
npm install -g @jgardner04/ghost-mcp-server
```

3. In Ghost Admin, go to Settings, then Integrations, then Add custom integration. Name it `Newsroom`. Copy the Admin API key.
4. In your terminal, connect it to Claude Code. Replace the placeholders:

```bash
claude mcp add ghost-mcp -- ghost-mcp-server --url https://your-ghost-site.com --key your-admin-api-key
```

5. Run `claude mcp list` and confirm `ghost-mcp` is connected.
6. Restart Claude Code and run a skill again.

Type the key into your own terminal only, never into the chat. The skills find your Ghost tools by the end of the tool name, so any server name works. A Ghost server with different action names fails the connection test.

## The three roles

- The plugin is the junior reporter. It researches and writes the first version.
- You are the senior reporter. You read each draft, fix the voice, and publish.
- The quality review is the editor. It reads what went out and tells you where the voice and the facts slipped.

## Save drafts

Setup recommends that new posts save as drafts, and the profile's post status is `draft` when you accept. Drafts let you revise before readers see a post. Your edits show you what to add to your voice rules. Choose `published` only when you trust the voice rules enough to skip the read.

## Reports

The quality review saves its reports to `~/.newsroom/reports/` and shows you the path each time.

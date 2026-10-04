# First-run setup

Run this when `~/.newsroom/publication-profile.md` does not exist. Do no other work until the interview ends. Run no web search and make no CMS write call. Keep the tone short and friendly. Ask one group of questions at a time.

## 1. Ask about the CMS first

Send this as your first message, before any other question:

> This plugin works with the content management system (CMS) your publication uses. Skills and Agents Co tests it with Ghost, and Ghost is the only CMS it supports today. Is your site on Ghost? If you want another CMS, email contact@skillsandagents.co and tell us which one.

If the user says the site is not on Ghost, say the plugin cannot save posts for that CMS yet. Repeat the address `contact@skillsandagents.co`. Save no profile. Stop the run.

## 2. Test the connection

Find a connected tool whose name ends in `posts_browse`. The server name in front of the suffix can be anything. Call it once with a limit of one post. Make no other call.

Report the result in one sentence. On success, name the site you reached if the response shows it, and say that setup made a read call only. Then go to step 4.

## 3. If the test fails

Say the connection test failed. Say why, if you know: no tool ending in `posts_browse`, or the call returned an error. A Ghost server that uses different action names also fails the test.

Show these steps, then stop the run. Save no profile.

1. Install Node.js 18 or later from nodejs.org. Run `node --version` to check.
2. Install the Ghost MCP server in a terminal:

```bash
npm install -g @jgardner04/ghost-mcp-server
```

3. In Ghost Admin, open Settings, then Integrations, then Add custom integration. Name it `Newsroom`. Copy the Admin API key and the API URL.
4. In a terminal, connect the server to Claude Code. Replace the two placeholders with your own values:

```bash
claude mcp add ghost-mcp -- ghost-mcp-server --url https://your-ghost-site.com --key your-admin-api-key
```

5. Run `claude mcp list` and confirm `ghost-mcp` shows as connected.
6. Restart Claude Code and run the same skill again.

Tell the user to type the key into their own terminal only, never into this chat.

## 4. Ask the publication questions

Ask these in one or two short messages. Offer an example for each.

1. **Publication name.** What is the publication called?
2. **Site URL.** What is the public address of the site? Use it for internal links. Check it against the site URL in the connection test result when you can.
3. **Verticals.** What topics does the publication cover? Two to six works best. Each vertical is a section heading and a tag.
4. **Tags.** For each vertical, which Ghost tag should posts carry? Call `tags_browse` once to list the existing tags and offer a match for each vertical. Tell the user to reuse an existing tag instead of making a new spelling of it. Ask for any topic tags that appear often.
5. **Title rules.** How should titles read? Offer this default: the title states the news in one clause and carries no opinion. Ask if the user wants a length range, a suffix, or words to avoid.
6. **Voice rules.** How should the writing sound? Ask for three to five rules, a sentence or two that sounds right, and phrases to never use. Offer to read a few of the site's recent posts with `posts_browse` and propose rules. Ask the user to confirm or edit what you propose.

## 5. Ask about post status

Ask whether new posts should save as drafts or publish right away. Recommend drafts, and explain the plan in these words:

> The plugin is your junior reporter. It researches and writes the first version. You are the senior reporter. You read each draft, fix the voice, and publish when you like it. The quality review is your editor. It checks the published work each week and tells you where the voice slipped. Drafts let you revise before readers see anything, and your edits teach you what to add to the voice rules.

If the user accepts, save `draft`. Save `published` only when the user says so in plain words.

## 6. Save the profile

Write the profile to `~/.newsroom/publication-profile.md`. Create the folder if it does not exist. Use the fields and layout in `references/publication-profile-template.md`. Write every answer the user gave. Leave no field blank: if the user skipped one, write the default from the template and say so.

Save the file only after steps 1 to 5 are done and the connection test passed. Never save a profile after a failed test.

Finish with a short message that shows the path `~/.newsroom/publication-profile.md`, lists what you saved in one line each, and says how to change it: edit the file, or ask to run setup again.

## 7. Secrets

Never ask for an API key, a password, or a token. Never write one to the profile. If the user pastes one into chat, tell them to rotate it in Ghost Admin and do not copy it anywhere.

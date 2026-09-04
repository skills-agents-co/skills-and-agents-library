# Catalog MCP endpoint

Skills and Agents runs an MCP server for org members who want to search and pull skills from an agent instead of the app.

**This endpoint isn't always on.** It sits behind a feature flag that's off by default in every environment, including production. Before wiring up a client, confirm with Skills and Agents that it's enabled for your org — otherwise you'll mint a token and get a not-found response with no explanation.

**Endpoint:** `POST https://app.skillsandagents.co/catalog/mcp`

**Tools:**
- `search_skills` — search your org's skills plus the public catalog by keyword. Returns a ranked list with slug, title, description, category, and how to install each one.
- `get_skill` — look up one skill by its slug. Returns full details plus an install command. It's designed to never return the raw skill file or a real token, just the command with a placeholder you fill in with your own token.

**Auth:** every request needs a bearer token, `Authorization: Bearer <your-token>`. There's no anonymous access. Mint your token from your org's Marketplace token settings page in the Skills and Agents app. Put it in the `Authorization` header only — never in a URL, and never in a config file you commit anywhere.

**Who this is for:** people who already have a Skills and Agents account and a token. This isn't a public discovery surface. If you don't have an account yet, go to [skillsandagents.co](https://skillsandagents.co) first.

`server.json` in this repo's root is a draft manifest for the public MCP registry (registry.modelcontextprotocol.io), so this endpoint can also show up there as a config reference. Check the registry directly to see whether it's live — this file doesn't track that.

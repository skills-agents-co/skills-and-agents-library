# Financial Pulse

A two-layer architecture for AI-driven personal and business finance analysis,
distributed as Claude Skills and Agents. MIT licensed.

- **Live directory:** https://skills.uristocrat.com
- **License:** [MIT](../LICENSE)

## What this is

1. **Financial Pulse (skill)** — the bank-agnostic analysis engine. Takes
   transaction data from any source, displays a categorized 30-day spending
   breakdown, and surfaces 3 specific things to look into based on 60-day
   trends.
2. **Bank connector agents** — thin wrappers that handle authentication and
   data retrieval for a specific bank's MCP server, then feed transactions into
   the Financial Pulse skill. Each bank that ships an MCP server gets its own
   connector.

The skill never connects to a bank directly. The connector agents handle the
bank-specific authentication and data retrieval, then run the shared analysis.

## Layout

```
financial-pulse/
├── skills/
│   └── financial-pulse/
│       └── SKILL.md                 # The analysis engine (bank-agnostic)
└── agents/
    ├── financial-pulse-grasshopper/
    │   └── SKILL.md                 # Grasshopper Bank connector (Narmi MCP)
    ├── financial-pulse-mercury/
    │   └── SKILL.md                 # Mercury connector (hosted MCP)
    └── financial-pulse-ramp/
        └── SKILL.md                 # Ramp connector (corporate card + expenses)
```

## Supported banks

| Bank | Connector | Type | Status | Auth |
|---|---|---|---|---|
| Grasshopper Bank | `financial-pulse-grasshopper` | Business banking | Live | Control Center token (Claude Desktop config) |
| Mercury | `financial-pulse-mercury` | Startup banking | Live (beta) | OAuth (hosted by Mercury) |
| Ramp | `financial-pulse-ramp` | Corporate card + expenses | Live | API credentials (self-hosted) |
| Any bank (CSV) | `financial-pulse` (base skill) | Universal | Live | Upload file |
| Meow Technologies | `financial-pulse-meow` | Agentic banking | Coming soon | — |
| Griffin (UK) | `financial-pulse-griffin` | UK business banking | Coming soon | — |

## Usage

Add the relevant `SKILL.md` to your Claude project context or system prompt. If
you bank with a provider that ships an MCP server, connect that MCP and use the
matching connector agent. Otherwise, use the base `financial-pulse` skill with a
CSV export or pasted transactions.

## Contributing a connector

New connectors follow the same pattern: a thin agent under `agents/` that
handles one bank's MCP authentication and data retrieval, then runs the shared
Financial Pulse analysis. Connectors should be read-only — never build write
capabilities, even where the bank's MCP supports them.

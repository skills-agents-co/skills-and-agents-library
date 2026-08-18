# Ads Copilot

A Claude Code skill that lets you chat with your ad-platform and analytics data, then returns ranked optimization recommendations. MIT licensed.

- **Live directory:** https://skillsandagents.co
- **License:** [MIT](../LICENSE)

## What this is

Ads Copilot is a lightweight "chat with your ads data" wedge. It is not an attribution platform, not a tracking pixel, and not a data warehouse. It discovers whatever ad and analytics sources are reachable in the session (connected MCP servers or pasted/exported CSVs), answers plain-language questions about performance, and returns specific, ranked moves to make.

Today, the Anthropic MCP registry has zero ad-platform connectors. Google Ads, Meta, TikTok, and LinkedIn are not one-click. GA4 and Stripe may be available depending on the user's setup. The skill is built to assume nothing — if MCPs are present, it uses them; otherwise it falls back to CSV exports.

## Layout

```
ads-copilot/
├── README.md
├── skills/
│   └── ads-copilot/
│       └── SKILL.md             # The chat-with-your-ads engine
├── scripts/
│   ├── parse_csv.py             # Normalize platform exports to a single schema
│   └── requirements.txt         # stdlib-only, see header comment
└── references/
    └── csv_schemas.md           # Expected column maps per platform
```

## Usage

Add `skills/ads-copilot/SKILL.md` to your Claude project context or system prompt. If you have any ad-platform or analytics MCP connected, the skill will use it. If not, export a CSV from the platform (see `references/csv_schemas.md` for which export to grab), optionally normalize it with `scripts/parse_csv.py`, and paste or upload the file.

### parse_csv.py flags

```
python3 scripts/parse_csv.py input.csv [options]
```

- `--platform {google,meta,tiktok,linkedin,ga4}` — override header-based platform detection.
- `--out PATH` — write to a file instead of stdout.
- `--decimal-sep {auto,period,comma}` — number-format convention. `auto` (default) heuristically detects US (`1,234.56`) vs European (`1.234,56`) formats. Set explicitly when the heuristic guesses wrong on ambiguous inputs.
- `--skip-rows N` — skip exactly N lines before the CSV header. N is not capped, so deep preambles (20+ lines) work. If omitted, the parser sniffs the first 15 lines and locates the header by matching cells against known platform tokens, which handles Google Ads UI exports with title/filter preamble rows.
- `--date-format FMT` — strptime format for the date column (e.g. `%m/%d/%Y`). Validated at startup — a bad directive (e.g. `%Q/%d/%Y`) exits with a clear error before any rows are read. Once set, the format takes precedence: a cell that doesn't match it is treated as a data error, not a cue to fall through to other formats. Required when slash-separated dates are ambiguous between month-first and day-first (e.g. `05/06/2026` or `05/06/26`).
- `--self-test` — run inline assertions over parser primitives and exit.

## Attribution honesty

Platform-reported conversions are self-reported. The skill cross-checks with GA4 and Stripe where those are connected, and never presents single-platform attribution as certain. If you only have one source, you only have one source — the skill says so.

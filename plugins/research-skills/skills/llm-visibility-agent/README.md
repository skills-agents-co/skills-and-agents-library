# llm-visibility-agent

Claude Code skill that reads Uristocrat's weekly AI Visibility report from the Amplitude / PostHog AI Visibility MCP, diagnoses where competitors win LLM answers, and recommends specific posts to close the gaps.

Pure read and synthesize layer. No crawling. No scraping. No model calls. The measurement engine already runs weekly via the MCP. This skill turns that data into editorial action.

## Install

Copy [`SKILL.md`](./SKILL.md) into a Claude Project's instructions, or load via the Uristocrat skills catalog.

## Requires

The Amplitude / PostHog AI Visibility MCP connected in the session. See [posthog.com/docs/ai-visibility](https://posthog.com/docs/ai-visibility).

## Trigger phrases

- "check AI visibility"
- "run the LLM visibility report"
- "AI search visibility brief"
- "/llm-visibility"

See `SKILL.md` for the full list.

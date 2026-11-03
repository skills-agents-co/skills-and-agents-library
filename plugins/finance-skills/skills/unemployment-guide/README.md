# Unemployment Guide

A free Claude Code skill that walks you through filing for unemployment insurance in any US state. Provides the official state agency name, application URL, phone number, eligibility rules, step-by-step application instructions, required documents, weekly certification rules, and the common pitfalls that cause denials — tailored to your state.

**Need help?** Email **skills@uristocrat.com** or visit **[skills.uristocrat.com](https://skills.uristocrat.com)**

---

## What it does

- Asks for your state and gives you the official agency name, online filing URL, and claimant phone number
- Lists the documents you need to gather before applying (SSN, ID, employer info, wages, bank routing — the full checklist)
- Walks you through the application portal step by step
- Explains the weekly (or biweekly) certification — the #1 reason people miss out on money they were owed
- Flags state-specific gotchas (Florida's Employ Florida pre-registration, Texas's 3-day WorkInTexas rule, California's EDD callback queues, ID.me verification, dependent allowances, etc.)
- Warns about the things that get claims denied: misclassifying "quit" vs "laid off", misconduct definitions, severance offsets, 1099 misclassification, refusing suitable work, working without reporting earnings
- Covers all 50 states plus DC

---

## Who it's for

Anyone who just lost their job and needs to file a claim correctly the first time. Unemployment systems are unforgiving — missing the work-search registration window, skipping a weekly certification, or describing your separation badly to the portal can cost you weeks of benefits. This skill is the guide a calm, knowledgeable friend would walk you through.

---

## Requirements

Just one thing:

- **[Claude Code](https://claude.ai/code)** — desktop app or CLI (free tier works fine)

No MCP servers, no browser extensions, no API keys.

---

## Installation

### Step 1 — Install Claude Code

If you don't have Claude Code yet:

1. Go to [claude.ai/code](https://claude.ai/code) and download the desktop app
2. Sign in with your Anthropic account (or create a free one)
3. Open Claude Code and confirm it launches

---

### Step 2 — Install this skill

Run this command in Terminal:

```bash
claude skills add https://raw.githubusercontent.com/uristocrat/unemployment-guide/main/SKILL.md
```

That's it. The skill is now installed and will trigger automatically when you mention being laid off, losing your job, or filing for unemployment.

---

### Step 3 — Use it

Open Claude Code and say one of these (or anything similar):

```
I just got laid off in California, what do I do?
```

```
lost my job in Florida last week, how do I file for unemployment
```

```
/unemployment
```

Claude will ask for your state (if you didn't include it), pull the right agency info, and walk you through filing.

---

## What it covers per state

For each state plus DC, the skill knows:

- Official unemployment agency name (EDD, DUA, DES, TWC, etc.)
- Online filing URL
- Claimant phone number
- Waiting period (1 week unpaid, or none)
- State-specific quirks worth flagging (work-search registration portals, max weeks of benefits, dependent allowances, ID.me requirements, biweekly vs weekly certification)

---

## What it warns you about

These are the most common reasons claims get delayed or denied. The skill flags them based on your situation:

- **Quitting vs laid off** — "Good cause" rules are narrow and vary by state. Describing your separation correctly is critical.
- **Fired for "misconduct"** — Performance issues usually don't legally count as misconduct. Apply anyway and let the state decide.
- **1099 / gig work** — Traditional UI doesn't cover contractors, but misclassification reviews are possible.
- **Severance offsets** — Some states reduce benefits dollar-for-dollar.
- **Not certifying weekly** — Most states won't let you back-certify. Miss a week, lose that week's payment forever.
- **Skipping work-search registration** — Many states require you register on their job board within 7 days of filing.
- **Identity verification** — ID.me bottlenecks block first payments. Get it done immediately.
- **Refusing "suitable work"** — Turning down a reasonable offer while collecting can end benefits.
- **Working without reporting** — Unreported earnings = fraud charge + repayment + penalty.

---

## Sources

The state agency information is built from publicly available data on each state's official Department of Labor / Workforce Agency site, cross-referenced with the [US Department of Labor's CareerOneStop](https://www.careeronestop.org/LocalHelp/UnemploymentBenefits/find-unemployment-benefits.aspx) finder.

Some details (max benefit amounts, exact waiting period rules, dependent allowance amounts) change with state legislation. If a phone number or URL looks dead, fall back to CareerOneStop — the DOL keeps it current.

---

## Disclaimer

This skill provides general procedural guidance based on publicly available information. It is **not legal advice**. State unemployment laws and policies change. For your specific situation — especially if you're appealing a denial, questioning a misclassification, or unsure how to characterize a separation — talk to your state's Bar Association's lawyer referral service, a legal aid clinic, or an employment attorney.

---

## Need help?

Email **skills@uristocrat.com** or visit **[skills.uristocrat.com](https://skills.uristocrat.com)**

---

## License

MIT — free to use, fork, and modify.

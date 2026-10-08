# Yahoo: UNTESTED

This file was written from Flaim's documented Yahoo behaviour, not from running the brief on a Yahoo league. Treat every line as a hypothesis. When a call returns something this file didn't predict, tell the user what happened and suggest they report it back to whoever shared the skill.

Flaim calls: platform `yahoo`, sport `football`.

## What Flaim documents

- **Transactions: a rolling 14-day window only.** `week` is ignored. Rows get `date`/`timestamp` once Yahoo stamps them; unstamped rows are dropped from most requests and counted in `dropped_invalid_timestamp_count`. `type: "waiver"` and `type: "pending_trade"` return the user's own pending items. `week` is null on Yahoo rows; assign the week from the date. **Capture every week without fail.** Anything older than 14 days is unreachable.
- **Rosters.** `team_id` is required. Historical weekly snapshots via `week`.
- **Matchups.** Summary only; `detail: "players"` is not supported. For lineups, use `get_roster` with `week`. Whether per-player weekly points come back that way is **unverified**; check on the first run and record the answer in the profile's "Known data gaps".
- **Standings.** `rank` is Yahoo's own standings order. Also `faabBalance` and `waiverPriority`. **Outcome fields (`finalRank`, `championshipWon`) are always null.** Ask the user for past champions rather than inferring from rank.
- **Free agents.** `percentOwned` is a **Yahoo-wide** market rate. Label it that way.
- **Keepers.** `isKeeper` may appear, but Yahoo has only been observed returning cost as false. No numeric keeper cost. Get keeper costs from the user.
- **League info.** `draftType`, `isAuctionDraft`, `canTradeDraftPicks` when Yahoo's settings fetch succeeds (omitted with a warning when it fails).
- **Drafts.** Confirmed results; no current pick-ownership ledger.

## League settings

Unverified which settings Flaim returns for Yahoo beyond `draftType`, `isAuctionDraft` and `canTradeDraftPicks`. Ask the user for scoring, waiver type and FAAB budget until a first run shows what's available. Yahoo's own settings page works as a fallback in the user's logged-in browser.

## What that means for the brief

Yahoo keeps the least history of the three platforms. On a first run, backfill standings and drafts, ask the user for past champions, and make the case for the weekly scheduled task: without it, the FAAB-pricing and waiver-yield analyses never get data.

## First-run checklist (help finish this file)

On the first Yahoo run, record in the profile:

1. Does `get_roster` with `week` return per-player points?
2. How many past seasons does `get_ancient_history` return?
3. Do transaction rows carry FAAB bids?
4. Anything that errored.

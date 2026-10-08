# ESPN

Flaim calls: platform `espn`, sport `football`. `season_year` is the single season year (2026 = the 2026 season).

## What Flaim gives

- **Transactions (current season only).** Structured source (`mTransactions2`) includes FAAB bids, failed bids and directional trade sides. Check `source` and `limitations`: if it has fallen back to `activity_feed`, failed bids and trade-lifecycle filters are unavailable. If the row count equals `count`, older rows may be missing; raise to 100 before claiming completeness. `week` means matchup period; week 0 is preseason.
- **Box scores.** `get_matchups` with `detail: "players"`, an explicit `week` and `team_id` returns both teams in that matchup: every player, lineup slot, started flag and points. Supported from 2018 on. This is the richest history ESPN offers.
- **Rosters.** `get_roster` with `week` gives a past snapshot, but its payload is large (full season stat lines). Prefer box scores for history.
- **Free agents.** `acquisitionState` (free agent vs on waivers) and `waiverClearsAt`. `percentOwned`/`percentStarted` are **ESPN-wide** rates across all ESPN leagues. Label them that way. A started rate is never conditional on being rostered.
- **Standings.** Verified `finalRank` and `championshipWon` for past seasons. ESPN standings don't report FAAB balances; compute remaining budget from captured transactions.
- **Keepers.** `get_league_info` reports keeper settings; `get_roster` reports `keeperValue` with a unit (auction dollars or draft round).
- **Drafts.** Confirmed picks with ESPN player IDs, no names. Resolve names from any box score or roster; ESPN player IDs are stable across seasons. No pick-ownership ledger.
- **Current projections, partly.** `get_free_agents` includes `projectedSeasonPoints` and `pointsPerGame`. `get_matchups` without `detail` returns each team's `totalProjectedPoints` for the current week. Per-player weekly projections for the user's roster aren't available (roster `stats` are actuals).
- **Injury status.** Current `get_roster` has `injuryStatus` per player. Box scores don't, past or present.
- **No owner names, scoring type or FAAB budget** in `get_league_info`. Ask the user.

## What Flaim doesn't give

- **Past-season transactions.** `ESPN_SEASON_NOT_SUPPORTED`. Capture weekly or lose them. See `history.md` for the reconstruction from box scores.
- **Per-player weekly projections** for rostered players, and any past projections.

## League settings through the browser

Flaim's ESPN `get_league_info` leaves out the scoring type, the waiver system and owner names. With the user logged in to ESPN in a browser the session can drive, open any `fantasy.espn.com` page and `fetch` with `credentials: 'include'`:

    https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/<Y>/segments/0/leagues/<LEAGUE_ID>?view=mSettings&view=mTeam

Read all of these (the setup checklist needs every one):

- `settings.acquisitionSettings`: `acquisitionType` (`WAIVERS_TRADITIONAL` = priority; FAAB leagues show a bidding type), **`isUsingAcquisitionBudget`** (the only reliable FAAB flag; `acquisitionBudget` is present even when unused), `waiverOrderReset`, `waiverHours`, `waiverProcessDays`, `waiverProcessHour`.
- `settings.scoringSettings.scoringItems`: the full table of `statId` → `points` (and per-position `pointsOverrides`, which is how TE premium shows up). Key IDs: `53` receptions (1 = full PPR, 0.5 = half, absent = standard), `4` passing TD, `3` passing yards per yard, `20` interception, `72` fumble lost, `24`/`25` rushing yards/TD, `42`/`43` receiving yards/TD.
- `settings.scheduleSettings`: `matchupPeriodCount` (regular-season weeks), `playoffTeamCount`, `playoffSeedingRule`, `playoffMatchupPeriodLength`, `divisions`.
- `settings.rosterSettings`: `lineupSlotCounts`, `positionLimits`, `lineupLocktimeType`, `moveLimit`.
- `settings.tradeSettings` (deadline, review hours, veto votes) and `settings.draftSettings` (type, auction budget, keeper count).
- Owners (only if the user wants handles): `members[].displayName` joined to `teams[].primaryOwner` (needs `view=mTeam`). No emails are returned.

Verified on a live league, Sept 2026. If the fetch returns 401, the user isn't logged in; ask them to log in to ESPN in that browser, or fall back to asking the settings directly.

## Optional: projections through the browser

Only if the user is logged in to ESPN in a browser the session can drive. From any `fantasy.espn.com` page, `fetch` with `credentials: 'include'`:

    Current season:  https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/<Y>/segments/0/leagues/<LEAGUE_ID>?scoringPeriodId=<W>&view=mRoster
    Past seasons:    https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/<LEAGUE_ID>?seasonId=<Y>&scoringPeriodId=<W>&view=mRoster

In each player's stats: `statSourceId 1` = projection, `0` = actual; `statSplitTypeId 1` = weekly (match `scoringPeriodId`), `0` = season. `defaultPositionId`: 1 QB, 2 RB, 3 WR, 4 TE, 5 K, 16 D/ST. For bulk pulls, accumulate into a `window` global across calls and save with a Blob and a clicked download link instead of routing large JSON through the conversation.

Check each season's projections for obvious corruption (a season where most players show 0) before computing anything from them.

Without the browser, get projections from a named public source and say which.

## Optional: trade details from email

If a trade comes back without sides and Gmail is connected, the league email (`from:fantasy@espnmail.com`) usually has them. Say the detail was recovered that way. ESPN doesn't email waiver bids, so this doesn't help with FAAB.

# League history: what exists, the backfill, the weekly capture

No database. Each league keeps a few small CSV files that the brief reads and appends to. The point of history is narrow: price FAAB bids against what this league actually pays, measure the user's real tendencies (waiver yield, lineup edge, trade record), and keep the decision log honest.

## What each platform gives through Flaim

Verified against real leagues in September 2026, except Yahoo.

| Data | ESPN | Sleeper | Yahoo (untested) |
|---|---|---|---|
| Past standings, records, points | Yes, back many seasons | Yes | Yes |
| Verified playoff finish / champion | Yes (`finalRank`, `championshipWon`) | Yes | **No** (outcome fields null; ask the user) |
| Past drafts | Yes (player IDs; resolve names from box scores) | Yes, plus current pick ownership | Yes, no pick ownership |
| Past-season transactions | **No.** Flaim returns `ESPN_SEASON_NOT_SUPPORTED` | **Yes**, per week (Flaim or public API) | **No.** Only a rolling 14-day window, even this season |
| Weekly box scores, starters + bench + points | **Yes**, 2018 on (`get_matchups` with `detail: "players"`, one matchup per call) | Starters only, no per-player points | Not supported; use `get_roster` with `week` for lineups |
| FAAB bids | Current season only | Yes | Current window only |
| Market ownership rates | ESPN-wide, current only | Not provided | Yahoo-wide, current only |

The two big platforms are gapped in opposite places. **ESPN** has rich past box scores but no past transactions. **Sleeper** has every past transaction but thin box scores. **Yahoo** keeps the least, so its weekly capture matters most.

## Backfill (at setup, once)

Run in this order. Stop and report if calls start failing. Don't loop on errors.

1. `get_ancient_history` for the list of seasons in this league.
1b. **Current-season transactions, week 0 to now** (`get_transactions` per week, `count: 100`). On ESPN and Yahoo these disappear after the season, so capture them first.
2. **Standings** for every season: `get_standings` per season → `seasons.csv`.
3. **Drafts** for the last three seasons, the user's picks only (`get_draft` with the user's `team_id`, far cheaper than the full board) → `drafts.csv`. ESPN returns player IDs only; resolve names from any box score or roster, since ESPN player IDs are stable across seasons. Leave unresolved names blank.
4. **The user's own box scores** for last season by default (a second season on request), where the platform supports it (ESPN: `get_matchups`, `detail: "players"`, the user's `team_id`, weeks 1 to the end of the regular season) → `my_weeks.csv`. This is about 14–17 calls per season, each one a whole matchup. Keep only the user's rows. ESPN box scores have **no position field**: take positions from the current roster, from `get_players`, or from where the player was slotted when started.
5. **Sleeper only:** every season's transactions, matchups and standings. With a browser, use the single in-page pass in `sleeper.md` and save only the summaries (Sleeper keeps the raw history, so it can be re-pulled any time). Without a browser, use Flaim `get_transactions` per week with `count: 100`, and say a week may be truncated if it returns exactly 100 rows.
6. **ESPN only, reconstructed moves:** diff consecutive weeks of the user's box-score rosters. A player appearing is an add or trade-in, a player disappearing is a drop or trade-out. Write these with `source=reconstructed` and no bid. Say clearly in any analysis that they're reconstructed and carry no FAAB.

League-wide box scores (every matchup, every week) are opt-in. On ESPN they cost one call per matchup: about 100 per season in a 12-team league.

## Weekly capture (every brief)

Append the week just finished, before analysing it:

- All transactions for the week, with bids and failed bids where the platform shows them → `transactions.csv` (`source=provider`).
- The user's box score → `my_weeks.csv`.
- Results for every matchup → `matchups.csv`.
- ESPN/Yahoo: this week's market rates for the user's roster and the top waiver candidates → `ownership.csv`. Rates are only useful as week-over-week moves, and there's no history of them unless it's captured.

**If a week was missed on ESPN or Yahoo, its bids are gone for good.** Say so in the brief rather than filling the gap with guesses, and suggest the scheduled task.

## Files

    seasons.csv       season, team_id, team_name, owner, wins, losses, ties, points_for, points_against, seed, final_rank, champion, outcome_confidence
    drafts.csv        season, round, pick, overall, team_id, owner, player_id, player_name, price_or_round, is_keeper
    transactions.csv  season, week, date, type, team_id, owner, added, dropped, faab_bid, failed_bid, trade_detail, source
    my_weeks.csv      season, week, player_id, player_name, position, lineup_slot, started, points
    matchups.csv      season, week, team_id, owner, points, opponent_id, opponent_points, result
    ownership.csv     date, week, player_id, player_name, position, pct_rostered, pct_started, available

Key everything on **team_id**, with the team name from that season (and the owner name if the user supplied one). Team names change every season; ESPN team IDs have stayed with the same franchise.

Blank means "not captured". Never write 0 for a missing bid or score. **Never leave a cell blank; a blank can't say why it's empty.** Write `NA` for not captured, `n/a` for not applicable (e.g. `faab_bid` in a waiver-priority league, `owner` when the user chose team names) and `none` for a real absence (a claim with no drop). In Google Drive, verify a write with `read_file_content`, not a search snippet: search previews collapse empty cells and look misaligned even when the sheet is fine.

## What to compute from it

- **FAAB market:** median season spend per team, price per claim by team, how many teams exhaust the budget, what a top-decile bid looks like. Recompute each preseason.
- **Waiver yield:** the user's adds, points per add, and spend per add, against the league. This is usually where a real leak shows up.
- **Lineup edge:** the start/sit test in SKILL.md, run on `my_weeks.csv`.
- **Trade record:** points gained and lost after each trade (Sleeper: full history; ESPN/Yahoo: from the season capture began).
- **Tiebreak stakes:** if seeds break on points-for, how often the margin was small.
- **Schedule luck:** the user's rank in points for and points against each season. A team that scores well and finishes .500 because it faced the most points in the league needs different advice from a team that's simply mediocre.

Report every figure with its sample size and the seasons it covers.

# Sleeper

Flaim calls: platform `sleeper`, sport `football`. **Sleeper creates a new league ID every season.** Match leagues by `recurringLeagueId` from `get_user_session` / `get_ancient_history`, and take the current season's ID from the session each time.

## What Flaim gives

- **Transactions for any season**, per week (`get_transactions` with `week`, `count: 100`). Includes FAAB bids and draft picks moved in trades. Timestamps are milliseconds UTC; convert to the user's timezone before stating a date. Flaim returns `teamOwners` (roster ID → username); use owner names in the brief.
- **Matchups** for the whole league in one call: each team's starters and total points. No bench and no per-player points.
- **Rosters** with starters, bench, reserve (IR) and taxi. Historical rosters need `team_id`.
- **Standings** with `faabBalance` (already reflects FAAB traded between teams, so it can exceed the starting budget) and `waiverPriority`. `0` means spent out; `null` means not reported, not "no FAAB".
- **Draft picks.** `get_draft` gives completed drafts and current pick ownership. `ownership.currentOwnerTeamId` is the current owner; a completed pick's `selectionTeamId` is the team that made it historically. `changed_picks_only` is not a full inventory: every roster also owns its own untraded picks. Label `provider_order_derived` placements as projected.
- **No market ownership rates.** Sleeper doesn't provide them. Skip the rostered-vs-started read on Sleeper and say so if asked.

## League settings

Flaim's `get_league_info` covers most of the checklist: the full `scoringSettings` table, `rosterPositions`, taxi and reserve slots, trade deadline, pick trading, keepers and traded picks. It does **not** return the waiver system, the playoff format or draft details. Get those from Sleeper's public API (no login). Open `https://sleeper.com/robots.txt` in the browser, then `fetch` from inside that page:

- `/v1/league/<id>` → `settings.type` (0 redraft, 1 keeper, 2 dynasty), `waiver_type` (2 = FAAB, otherwise rolling/reverse priority), `waiver_budget`, `waiver_bid_min`, `daily_waivers`, `waiver_day_of_week`, `waiver_clear_days`, `playoff_teams`, `playoff_week_start`, `playoff_seed_type`, `playoff_round_type`, `league_average_match` (1 = teams also play the weekly median), `best_ball`, taxi and reserve settings, plus `previous_league_id`.
- `/v1/league/<id>/drafts`, then `/v1/draft/<draft_id>` for each → `type` (snake / linear / auction), `settings.rounds`, `settings.budget` (auction), `settings.player_type` (1 = rookies only), `settings.reversal_round`.

Loop from the current season back through `previous_league_id` until it's empty or "0", collecting the same fields for every season. Verified on a live league, Sept 2026: four seasons, where the lineup gained a TE slot, taxi was added in year two, and drafts went from a 25-round snake startup to 4-round linear rookie drafts.

Sleeper usernames come through Flaim (`teamOwners`, `ownerName`). There are no emails.

## FAAB: read the budget, not the claim log

Sleeper files every offseason claim (May to early September) under Week 1. In the tested league those offseason claims **don't count against the in-season budget**: the claim log summed to more than $1,000 for some teams, while each roster's `settings.waiver_budget_used` matched only the in-season claims. So:

- **Remaining budget:** use Flaim `get_standings.faabBalance` (or the roster's `waiver_budget_used`). Never sum the claim log.
- **What the league pays:** price bids from in-season claims (Week 2 on) separately from offseason ones. Offseason bidding runs much hotter.
- Still check the budget figures each season; a league could count offseason claims.

## What Flaim's Sleeper data can't do (and the browser fix)

- **Free agents:** Flaim returns them alphabetically, with no projections, and includes retired players. Rank available players in the browser instead: every player not on any roster (`/v1/league/<id>/rosters`, counting `players`, `taxi` and `reserve`), with an NFL team and `status: Active`, ranked by this week's projection, plus Sleeper's trending adds (`/v1/players/nfl/trending/add?lookback_hours=48`).
- **Injury status:** Flaim's Sleeper roster has none. Use `/v1/players/nfl` (`injury_status`, `injury_body_part`, `years_exp`, `depth_chart_order`), then confirm with news.
- **Projections:** `https://api.sleeper.app/projections/nfl/<season>/<week>?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF` (unofficial). Use the stat that matches the league's reception scoring: `pts_ppr`, `pts_half_ppr` or `pts_std`.
- **Per-player points and bench:** `/v1/league/<id>/matchups/<week>` has `players`, `starters` and `players_points`, which is enough for the lineup analyses.
- **Standings phase:** Flaim reported `seasonPhase: "playoffs_in_progress"` and `madePlayoffs: true` for the top six in Week 3. Ignore those two fields before the playoffs start.

## Backfill on Sleeper: one browser pass, summaries saved

Every Sleeper season stays reachable, so there's no need to store raw rows. In one in-page script (start it, store results in a `window` global, poll a status flag rather than awaiting a long call), pull for each season: users, rosters, `winners_bracket`, transactions for weeks 0–18, matchups, and `/v1/players/nfl` once for names and positions. Then compute the summaries **in the page** and bring back only those: season standings with champions, the FAAB market, the user's weekly actual vs optimal lineup and median results, trades by owner, and the pick ledger. That keeps thousands of rows out of the conversation. Flaim's per-week calls work too, but take about 80 calls for four seasons.

## Dynasty and keeper

- **Open IR slots:** if a player with an IR designation sits on the bench while IR slots are open, say so. Moving him frees a roster spot.
- **Taxi eligibility needs draft history:** `/v1/draft/<id>/picks` shows who drafted each rookie. A player acquired by trade may fail a house rule like "drafted or signed by this team", even though Sleeper allowed the move.

- **Taxi rules come from the user, not the settings.** Many leagues add rules Sleeper doesn't enforce (e.g. a player can't return to taxi once active, taxi closes after a set week). Record them in the profile and confirm every condition before a taxi recommendation. Flaim can't show whether a player has ever been on the active roster; ask the user.
- **Pick ledger.** Build it from `get_draft` ownership plus "every roster owns its own untraded picks", for as many future seasons as the league allows trading. Keep it in `planner.md`.
- **The window.** Record whether the team is contending, rebuilding or in between, and why. Every long-range recommendation has to respect it. A team with no picks adds young talent mainly through undrafted rookies signed right after the rookie draft and stashed on taxi.
- **Superflex:** in this skill's test league, the biggest FAAB bids ever were panic claims on backup QBs that returned little. Holding a real third QB beats winning those auctions. Check whether the user's league has the same pattern before citing it.
- **Be slow to drop tight ends.** In the test league, TEs were over-represented among the worst drops in league history. Check the user's own league before citing it.

## Rookie draft cycle (dynasty)

1. **Calibrate from this league's own drafts:** how deep it goes at each position and how early QBs go in superflex.
2. **After the combine:** seed a rookie board with college production, athletic testing and a consensus big board. Paid sources only work through the user's logged-in browser; test access before relying on one.
3. **After day three of the NFL draft:** re-rank on draft capital and landing spot. The question for deep rookies is whether there's a path to snaps before taxi eligibility runs out.
4. **Before the league draft:** publish the final board, plus the undrafted free agent board with taxi eligibility confirmed and open taxi slots stated. Rebuild the pick ledger.

## Optional: per-player points through the browser

Flaim's Sleeper matchups have no per-player points, so the bench-regret and lineup-edge analyses need the public Sleeper API (`https://api.sleeper.app/v1/league/<id>/matchups/<week>` returns `players_points`). From a cloud shell it's often blocked. A route that worked: open `https://sleeper.com/robots.txt` in a browser the session can drive (a static page won't redirect mid-script), run an async `fetch` loop against `api.sleeper.app` inside the page, stash results in a `window` global, poll a status variable rather than awaiting a long script, and save with a Blob and a clicked download link. The same route gives `/players/nfl` (keep name, position, team, birth_date, years_exp) for real ages, which Flaim doesn't have.

Without it, say that lineup-edge analysis isn't available on this league.

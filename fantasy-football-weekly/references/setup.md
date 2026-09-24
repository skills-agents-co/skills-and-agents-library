# First-run setup

Run this when no league profile exists. Keep it conversational and short. Most answers come from the platform. The user only confirms what the platform showed and fills in what it can't see.

## 1. Find the leagues

Call `get_user_session`. Show the user their leagues by name, platform and season (never IDs). Ask which ones the brief should cover and which is the default. Each league gets its own profile. If Flaim shows no leagues, tell the user to link their account in Flaim and run `refresh_leagues` afterwards.

## 2. Pull every league setting automatically

The user should never have to type in a setting the platform knows. Fill the whole checklist below from the platform, show the result, and ask the user only to confirm it. Ask the user to fill a line only if every source for it failed, and say which source failed.

**Sources, in order:**

1. **Flaim `get_league_info`** (plus `get_standings` for seeds and FAAB balances). Always first.
2. **The platform's own settings through the browser**, for whatever Flaim left out. ESPN needs the user logged in to ESPN in that browser. Sleeper's settings are public, so no login is needed. The exact endpoints and field names are in the platform file, under "League settings".
3. **The user**, only for lines still empty, and for house rules no platform stores (step 5).

**The checklist.** Every line gets a value and a source:

| Setting | ESPN | Sleeper |
|---|---|---|
| Teams, divisions | Flaim (teams); browser `scheduleSettings.divisions` | Flaim `totalRosters` |
| Scoring: full scoring table, not just "PPR" | **browser** `scoringSettings.scoringItems` | Flaim `scoringSettings` (complete) |
| Starting lineup, bench, IR, taxi | Flaim `roster.lineupSlotCounts` | Flaim `rosterPositions`, `leagueFormat.taxi`, `reserveSlots` |
| Waiver system: FAAB or priority, budget, order reset, process days | **browser** `acquisitionSettings` | **browser** `waiver_type`, `waiver_budget`, `waiver_day_of_week`, `daily_waivers` |
| Regular-season length, playoff teams, playoff start, seeding tiebreaker | Flaim `schedule.playoffSeedingRule`; **browser** `scheduleSettings.playoffTeamCount`, `matchupPeriodCount` | **browser** `playoff_teams`, `playoff_week_start`, `playoff_seed_type` |
| Median / league-average game | n/a on ESPN | **browser** `league_average_match` |
| Lineup lock | **browser** `rosterSettings.lineupLocktimeType` | per-game on Sleeper |
| Trade deadline, review, vetoes | Flaim `tradeSettings` | Flaim `leagueFormat.tradeDeadlineWeek` |
| Draft type, auction budget, keepers | Flaim `draftSettings`, `keeperSettings` | Flaim `leagueFormat` (+ `get_draft`) |
| Pick trading, future pick ledger | none | Flaim `leagueFormat.pickTrading`, `tradedPicks` |
| League format each season (redraft / keeper / dynasty) | Flaim `keeperSettings` | **browser** `settings.type` per season (0 redraft, 1 keeper, 2 dynasty) |
| Draft each season: snake / linear / auction, rounds, budget, rookies-only or all players | Flaim `get_draft` per season (`draft.type`) + `draftSettings` | **browser** `/league/<id>/drafts` then `/draft/<id>`: `type`, `settings.rounds`, `settings.budget`, `settings.player_type` (1 = rookies only), `settings.reversal_round` |

**Walk every season, not just this one.** Leagues change settings between years (a TE slot added, taxi introduced, scoring tweaked). Pull the checklist for each past season too and record a one-line **settings history** in the profile, so history is read against the rules that applied that year. On Sleeper every season is a separate league ID: follow `previous_league_id` back to the first season. This works the same for redraft, keeper and dynasty leagues. ESPN keeps one league ID and takes a season parameter.

**Read the whole scoring table, then summarise what matters.** Points per reception, passing TD value, interception and fumble penalties, bonuses, TE premium, superflex or 2-QB, kicker and D/ST rules. These change player values, so the brief must use them: a 4-point passing TD league values QBs differently from a 6-point one.

**Never infer a setting from activity.** A column of $0 bids doesn't mean waiver priority. A budget field doesn't mean FAAB is on: ESPN stores a $100 budget even when `isUsingAcquisitionBudget` is false. A non-null `faabBalance` doesn't settle it either. Read the setting itself.

**Re-pull settings at the first run of each season**, and whenever something in a brief contradicts the profile (a bid in a "priority" league, a lineup slot that doesn't exist). Leagues change rules between seasons.

**If no browser is available:** fill what Flaim gives, then ask the user to confirm only the missing lines, grouped into one short question. Say that connecting a browser would let the skill read them directly next time.

Note leagues with no IR slots: players on IR then take up bench spots, which changes drop decisions.

## 3. Team and owner names

**Default to team names.** They're always available and need nothing from the user. Offer, once, to record real owner names instead. If the user supplies them, key them to `team_id` (stable across seasons on ESPN; Sleeper and Yahoo give usernames).

What each source can identify, so you don't promise more:

- **Flaim:** Sleeper returns usernames (`teamOwners`). ESPN returns team names only. Yahoo is untested. **Flaim returns no email addresses on any platform.**
- **ESPN through the browser:** league members' display names (handles) and each team's `primaryOwner` member ID. No emails. Use handles only if the user asks for them; don't collect members' real names.

Team names change every season, so ledgers always carry `team_id` and the history uses the name from that season.

## 4. Where files live: ask every run

**Ask the user where to save at the start of every run**, with a recommended option first. Recommend, in order:

1. **The location saved in the profile** from the last run, if there is one.
2. **Google Drive** (when the Drive connector is available), otherwise.
3. **A folder on this computer**, when the session can reach one and Drive isn't available.

Options to explain the first time:

- **Google Drive.** Works from any session, including scheduled runs in the cloud. Drive has no in-place edit: to revise a file, read it, merge the full text, create a new file with the same title and parent, verify it, then trash the old one. Resolve files by folder + exact title, never by a remembered file ID, because every revision gets a new ID. Two files with the same title means stop and report it.
- **A folder on this computer.** Best for chats on that computer. A scheduled cloud run can't reach it unless the task is set to require the computer.
- **Neither.** Deliver the files in the chat. Tell the user plainly that history won't accumulate this way.

If the user picks a new location, record it in the profile. Don't move old files without asking. A scheduled run has no one to ask: it uses the profile's location and says so in the brief.

Layout, one folder per league (or the folder the user points at, used directly):

    <storage>/fantasy-weekly-brief/
      <league-slug>/
        profile.md
        planner.md              (dynasty/keeper leagues only)
        decision_log.md
        history/                (see history.md)

## 5. Interview for what no platform sees

Ask only the questions that apply, a few at a time:

- **Rules the platform doesn't enforce.** Keeper costs and limits, taxi eligibility beyond the platform setting (e.g. "never been on the active roster"), trade-review rules, house rules. Record them in the user's words.
- **Any checklist line every source failed on** (rare; see step 2).
- **For dynasty/keeper:** the team's window (contending now, rebuilding, in between), picks traded away or acquired, players the user considers untouchable.
- **Hard nos:** players they'll never roster, strategies they've ruled out.
- **Format preference:** prose paragraphs or compact bullets.
- **Anything about the other owners** they want the brief to know. Optional.

## 6. Offer the history backfill

Explain in two sentences what the platform keeps and what it doesn't (see `history.md`), then offer the backfill. League-wide box scores are opt-in because they cost one call per matchup.

## 7. Offer the weekly scheduled task

For ESPN and Yahoo leagues this matters most: their transactions and bids can only be captured while they're live. Offer a weekly scheduled task (the day after waivers process) that runs the capture and writes the brief. A cloud-scheduled task can only write to Google Drive, or to a local folder if the task is set to require the user's computer.

## Profile template

Use plain labelled lines, not YAML front matter: Google Docs converts a `---` block into a heading and merges the lines, so a later run can't read it back.

    # <league name> — league profile

    ## League
    Platform: espn | sleeper | yahoo
    League ID: <id>            (Sleeper: the recurring league id)
    Team ID: <the user's team id>
    Format: redraft | keeper | dynasty
    Default league: yes | no
    Storage: <last location used; recommended first next run>
    Owner names: team names | user-supplied
    Output style: prose | bullets

    ## Settings
    One line each, with its source (Flaim / browser / user) and date:
    scoring (full summary), waiver system and budget, draft type,
    starting lineup, bench/IR/taxi, lineup lock, divisions,
    regular-season length, playoff teams and start, seeding tiebreaker,
    median game, trade deadline and review, pick trading.

    ## Confirmed rules (from the user)
    ## Hard nos
    ## Team situation          (window, picks, core players; dynasty/keeper)
    ## Owners                  (team_id → name, only if the user supplied them)
    ## Known data gaps

Keep the profile short. It's read on every run. After writing it to Drive, read it back and check the League section is still one line per field.

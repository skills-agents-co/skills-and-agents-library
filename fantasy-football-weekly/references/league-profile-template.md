# League profile: <league name>

Copy this file to `references/<league-slug>.md` and fill it in. Mark anything unverified as `(unverified)`.

## Identity

- default: yes | no   (use when the manager has several leagues)
- Manager name:
- Platform: ESPN | Sleeper | Yahoo | other
- League id:
- Manager's team id:
- Other leagues the manager plays in (and whether this is the default):

## Format

- Teams:
- Draft type: snake | auction ($ budget) | keeper | dynasty
- Scoring: standard | half PPR | full PPR | other bonuses
- Starting lineup (every slot):
- Bench / IR slots:
- Position caps (for example max QBs rostered):
- The one or two format facts that matter most:
- Playoff seeding tiebreaker:

## Waivers

- System: FAAB | rolling priority | reverse standings
- FAAB budget per team per season:
- League spend history (median season spend, typical $/claim, outlier threshold):
- Manager's own waiver behaviour (adds per season, spend, yield per add):

## Data sources

| Need | Tool / path |
|---|---|
| Roster, matchup, free agents, transactions | |
| Last week's player scores + started flags | |
| Projections (weekly + season), and how to pull them | |
| Ownership snapshots (rostered / started %) | |
| League history database | |
| Trade detail fallback (for example league emails) | |

Known capture bugs or gaps:

## Private storage

- Decision log location (must be reachable from wherever the weekly run executes):
- Kickoff analysis save location:
- Any shared/public league output that must NEVER receive data from this brief:

## League-measured findings

Record tested results here with their numbers (start/sit edge by position, D/ST base rates, projection accuracy, close-game rate, etc.). Record failed hypotheses too.

## Manager tendencies

What the data says they're good at, what's a real leak, and what was tested and turned out NOT to be a problem.

## Failed recommendations log

Recommendations from this brief that failed on review, one line each, with the lesson.

## League context

- How to refer to teams (owner names vs team names):
- Notable rivals (most active traders, best lineup setters):

# Dynasty window check: push, hold, retool or rebuild

**Dynasty leagues only** (and keeper leagues, in a lighter form: see the end). Skip this for redraft leagues.

Every weekly brief in a dynasty league ends with a short window check. It says which of four stances fits the team right now, why, and the one or two moves that fit it. The stance comes from two separate questions, answered with data rather than feel:

1. **Can this team win the title this season?** A season simulation gives playoff odds and title odds.
2. **What is this roster worth, and how long will that last?** Market trade values, the age of the core, and pick capital.

A team can be strong on one and weak on the other: good now but old (sell before the cliff), or bad now but young and rich in picks (be patient). That split is the whole point.

## 1. Season odds: simulate the rest of the season

Run it in the browser (in-page JavaScript), not in the chat. 10,000 simulations take about a second.

- **Team strength.** For each team, take its best possible lineup under this week's projections (Sleeper's projections endpoint, or ESPN's through the browser; see the platform files). Blend that with the team's actual scores so far, weighting the projection as worth two games: `strength = (2 × projected + sum of actual scores) / (2 + games played)`. Use `pts_ppr`, `pts_half_ppr` or `pts_std` to match the league's scoring.
- **Uncertainty.** Every simulation draws each team's true strength once, with a spread that shrinks as the season goes on: SD = 14 / √(1 + weeks played / 4). Then each game adds a weekly spread of about 24 points. **Without the team-level spread the odds come out overconfident.** In testing, the first version showed 100% playoff odds after two weeks.
- **The league's real format** from the profile: remaining schedule (Sleeper `/matchups/<week>` lists future pairings; ESPN via Flaim `get_matchups` for future weeks), median games if the league has them (top half of scores each week gets a win), number of playoff teams, byes, and the seeding tiebreaker.
- **Output per team:** playoff %, title %, and rank. Report the user's line and the league's top three.

Before about Week 4, say the odds lean mostly on projections.

## 2. Roster value, age and pick capital

- **Market values:** FantasyCalc's public dynasty values, fetched in the browser with the league's format:
  `https://api.fantasycalc.com/values/current?isDynasty=true&numQbs=<1, or 2 for superflex/2QB>&numTeams=<teams>&ppr=<0, 0.5 or 1>`
  Each entry has `player.sleeperId` (match Sleeper rosters directly; match ESPN players by name and position), `player.maybeAge`, `player.position` and `value`. It also values draft picks by year and round ("2027 1st", "2027 2nd"...). Verified Sept 2026. It's an unofficial public API. If it fails, fall back to age and production, and say the values are missing.
- **Team value** = player values + the value of every future pick the team owns (use the pick ledger: own picks not traded away, plus picks acquired). Rank all teams.
- **Core age:** the value-weighted average age of the team's 11 most valuable players.
- **Value near the cliff:** the share of player value in players within a year of the usual age drop-off: RB 26+, WR and TE 29+, QB 33+. These are rough rules of thumb, so report the share and name the players rather than treating the cutoff as exact.

## 3. The four stances

| Stance | Typical signs | What it means |
|---|---|---|
| **Push** (all-in) | Title odds at least twice the league average (100% ÷ teams), or playoff odds 75%+ with team value in the top third | Buy starters for this season. Pay with picks, prospects, or depth that won't start. |
| **Hold** | Playoff odds roughly 40–75%, value mid-pack | Make only moves that help now *and* later. Don't sell core players, don't overpay for rentals. |
| **Retool** (partial rebuild) | Playoff odds under ~40%, but team value in the top half; or a high share of value near the cliff | Sell players near the cliff while their value holds, keep the young core, add picks and young players. Aim to contend again next season. |
| **Rebuild** (full) | Playoff odds under ~20% and team value in the bottom half, or an old core (value-weighted age 28+ with 30%+ of value near the cliff) | Turn every non-core veteran into picks and young players. Take losses now. Plan around the rookie draft. |

These are starting points, not formulas. When signals conflict (say, strong odds but an old core), say so and explain which one should win and why.

**Guardrails**

- **Don't flip-flop.** Change the stance only after the new verdict has held two weeks running, unless the trade deadline is within two weeks.
- **The user's stated plan wins, and the data gets its say.** If the profile says "title push" and the numbers say retool, report the disagreement plainly with the numbers, then work within the user's plan unless they change it.
- **Deadline countdown.** From four weeks before the trade deadline, say how many trade windows are left. After the deadline, the stance carries into the offseason: the rookie draft, the summer trade market, and which players to sell before they age.
- **Values are market consensus, not truth.** Use them to spot mismatches (a player the market prices well above his role, or below it), not to grade trades mechanically. The existing trade rules still apply: stress-test both sides, and don't fix a direct rival's hole unless the user clearly wins.

## 4. Turning the stance into moves

Label every other team with its own stance from the same data; this gives the trade map.

- **Push:** buy from teams in retool or rebuild, targeting their near-cliff starters, who are usually cheapest for a contender. If the user has no picks, name exactly which bench or depth players would pay for it.
- **Retool / rebuild:** sell near-cliff players to teams in push, especially the ones missing that position. Ask for picks from teams likely to finish low (their picks will land early) and for young players.
- **Hold:** look for trades that swap one old starter for a younger one of similar value.

At most two concrete moves a week. "No move" is a valid answer.

## 5. Output: "Window check" section of the brief

Three or four sentences:

1. The stance, the user's playoff and title odds with their rank, and team value rank.
2. The one or two facts driving it (for example: youngest core among contenders, no pick capital, 38% of value near the cliff).
3. The fitting move or moves, with which teams are the natural partners and why.
4. What would change the call (for example: "two more losses, or an injury to either QB, moves this to hold").

## Keeper leagues

Use the same odds simulation. Replace dynasty value with next season's keeper value: players the user could keep, what each costs (from the profile's keeper rules), and whether the team is better off trading for players it can keep. The stances collapse to two: push this season, or position for next season's keepers and draft.

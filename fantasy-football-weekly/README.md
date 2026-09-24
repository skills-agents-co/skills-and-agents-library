# fantasy-football-weekly

Version 1.5 (September 2026). Built against the Flaim connector as of that date; if Flaim's tools change, parts of this skill may need updating.

A Claude skill that writes a private weekly brief for your own fantasy football team (start/sit, waivers with FAAB bids, trades, league recap, draft review, and for dynasty leagues a weekly push-or-rebuild check) and keeps a small history of your league so its advice gets sharper each season.

## You need

- **Claude with skills enabled.** Upload this folder as a skill (zip it if your Claude app asks for a zip).
- **The Flaim connector**, with your ESPN, Sleeper or Yahoo account linked in Flaim. The skill reads all league data through it.
- **A place for files:** a folder on your computer, or Google Drive (needed if you want a weekly scheduled run from the cloud).

## Platforms

- **ESPN:** tested end to end (setup, history backfill, weekly brief).
- **Sleeper:** tested end to end (setup, four-season history, weekly brief) on a dynasty superflex league.
- **Yahoo:** untested. It should work, but expect rough edges. The skill will tell you when something behaves unexpectedly.

## Getting started

Ask Claude for "my weekly fantasy brief". The first run lists your leagues, reads all your league settings from the platform for you to confirm, asks only about house rules no platform stores, offers to backfill your league history, and offers to set up a weekly scheduled run.

## Good to know

- **First setup takes a while:** roughly 40–50 Flaim calls to backfill a league's history. Weekly runs after that are much lighter.
- **Optional browser features** (ESPN league settings and projections, Sleeper per-player points) read the platforms' own web data through your logged-in browser. These aren't official, documented APIs and can change without notice. The brief works without them.
- **Advice is decision support, not a guarantee.** It explains its reasoning so you can overrule it.

## Privacy

The skill contains no one's league data. Everything it learns about your league stays in the files you point it at.

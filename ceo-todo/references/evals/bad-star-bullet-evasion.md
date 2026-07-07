# CEO To-Do — Single Source of Truth

last updated: 2026-07-06

# EVASION FIXTURE (bad). The second item uses a * bullet instead of -. Before the
# item-gate fix this line was silently skipped (invisible), so its violated
# invariant went undetected — a fully-populated dangerous doc read as "0 items,
# VALIDATION PASSED". Now it must be parsed and caught: it is a P0 OPEN item 35
# days old that was never re-tagged as stale.

## Now

- [OPEN] [#a1b2] P0 · Approve the Q3 board deck and send to Dana · updated: 2026-07-05
* [OPEN] [#beef] P0 · Vendor wire nobody re-checked in weeks · updated: 2026-06-01

## Archive

- [DONE] [#9012] P1 · Sign the office sublease extension · updated: 2026-06-18

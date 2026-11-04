# Web Routes: Parlay Tracker

Public, like the other tabs.

## `GET /parlays`

Renders the Parlays tab inside the shared layout. The tab bar shows Records, Transactions, Bench
and Parlays. No query parameters; no season dropdown (FR-010).

**With no parlays recorded**: heading, intro, and "No parlays recorded yet."

**Above the table**:
- Heading "Who keeps busting the parlay?", then the line: "Each week the lowest scorer shotguns,
  puts $10 on a parlay and picks the category. Everyone picks one leg."
- Summary line: "**N of M** parlays hit" (settled only), plus ", paying $X" when any hit.

**Table**: one row per member, ranked per research §6.

| Column | Format |
|--------|--------|
| Member | full name |
| Record | `W-L` of graded legs |
| Hit % | whole percent, or – |
| Odds said | expected hit rate, whole percent, or – |
| Killed | parlay-killer count, bold |

**Footnote**: "Odds said = how often the odds expected their legs to hit. Killed = parlays where
theirs was the only losing leg."

**Weeks**: below the table, newest first (season, then week). Each week:
- Heading: "Week N" (with the season, `Week N, 2026`, once more than one season is recorded),
  then the result: "Hit · paid $X", "Busted" or "Pending".
- "**LSP**'s category: <category>"
- One row per leg, in file order: the member's name with the pick below it, the odds (`+240`,
  `−150` or blank), and the result (✅, ❌, or "pending"). The sole loser's leg is marked
  "killed it".

Always 200.

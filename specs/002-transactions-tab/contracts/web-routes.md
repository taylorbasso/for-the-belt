# Web Routes: Transactions Tab

Public, like Records: no login, no forms beyond the season dropdown.

## `GET /transactions[?season=<year>|all]`

Renders the Transactions tab inside the shared layout. The tab bar shows Records and
Transactions, and the current tab is highlighted.

**Season dropdown**: the same one Records uses (see
[001 web-routes](../../001-historical-records/contracts/web-routes.md)):
- It lists every season, newest first, then "All time".
- It defaults to the current season.
- An unknown year falls back to the current season.

**Table**: one row per manager who played in the selected seasons, in FR-006 order.

| Column | Format |
|--------|--------|
| Manager | full name; wraps rather than widening the table |
| Pickups | integer |
| Drops | integer |
| Trades | integer |
| Lineup | integer (lineup moves) |
| IR | integer (IR moves) |

**Footnote**:
- "Pickups include waiver claims and free agents. A trade counts once for each manager in it.
  Lineup = players moved into the starting lineup. IR = players moved to injured reserve."
- "<year> season in progress." Shown on the current season or All time while the season is
  live.
- "Updated <time>."

**When ESPN is unavailable**: same as Records. Show cached counts with "Couldn't reach ESPN.
Showing counts as of <time>.", or just "Couldn't reach ESPN. Try again later." with nothing
cached. Always 200.

## `GET /records`

Unchanged. Its dropdown now comes from the shared partial.

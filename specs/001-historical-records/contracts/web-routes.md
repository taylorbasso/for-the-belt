# Web Routes: Historical Records

All routes are public: no login (FR-011), no forms, no sessions.

## `GET /`

Redirects (302) to `/records`. It's the only tab for now; once the bet tracker exists, this
will point at whichever tab the league uses most.

## `GET /records[?season=<year>|all]`

Renders the Historical Records tab inside the shared layout. A "Season" dropdown above the
table (FR-013) lists every season, newest first, then "All time"; changing it reloads the page
with `?season=`. With no `season`, or one ESPN doesn't have, the page shows the current season.
A single season hides the Yrs column, and its in-progress note only appears for the current
season. The layout has a tab bar
(one tab for now) and the app's title, "For the Belt".

**Table**: one row per manager, in the FR-007 order.

| Column | Format |
|--------|--------|
| Manager | full name; wraps rather than widening the table |
| Yrs | integer |
| W-L-T | e.g. `39-24-0` |
| Win% | three decimals, e.g. `.619` |
| PF / PA | whole numbers, e.g. `6946` |
| Titles | integer; a 🏆 for each title is fine |
| 🍺 | shotguns (FR-012), integer |

**Footnotes under the table**:
- "Records are regular season only. 🍺 = shotguns: weeks with the league's lowest score,
  playoffs included."
- If the current season is in progress: "<year> season in progress."
- "Updated <time>": when the current season was last fetched.

**When ESPN is unavailable**:
- With cached data: the table renders normally, plus a notice: "Couldn't reach ESPN. Showing
  records as of <time>."
- With nothing cached: the page shows only the notice "Couldn't reach ESPN. Try again later."
- Either way, the status is 200 (never an error page).

**Layout**: at a 375px-wide viewport, the page doesn't scroll sideways (FR-009).

## `GET /healthz`

Returns `ok` (200). It never calls ESPN. The ALB target group and the container health check
use it.

## Configuration (environment variables)

| Variable | Local (`.env`) | Deployed |
|----------|----------------|----------|
| `ESPN_LEAGUE_ID` | yes | plain task environment variable |
| `ESPN_S2` | yes | SSM SecureString `/for-the-belt/espn-s2` |
| `ESPN_SWID` | yes | SSM SecureString `/for-the-belt/espn-swid` |

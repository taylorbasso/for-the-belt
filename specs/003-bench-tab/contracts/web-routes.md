# Web Routes: Bench Tab

Public, like the other tabs.

## `GET /bench[?season=<year>|all]`

Renders the Bench tab inside the shared layout. The tab bar shows Records, Transactions and
Bench.

**Season dropdown**: the shared one (see
[001 web-routes](../../001-historical-records/contracts/web-routes.md)). It defaults to the
current season.

**Above the table**:
- Heading "Who can't set a lineup?", then the line: "Each week, your lineup vs. the best one you
  could have started from your own roster (in hindsight). The gap is points you left on the
  bench."
- A callout labeled "🤡 Worst lineup of <year>" or "Worst lineup ever" (All time). It holds the
  single worst manager-week as a sentence: "**Name**, week N[ of YYYY]: started <starter>
  (pts) over <bench player> (pts), leaving **X points** on the bench."

**Table**: one row per manager, worst first (FR-007).

| Column | Format |
|--------|--------|
| Manager | full name. Below it, a small muted line: `Worst: wk 4 (−41.6), started Saquon Barkley (1.0) over Alvin Kamara (17.8)`. On All time the week includes the year (`wk 5 '24`). There's no line when the manager never left points on the bench. |
| Points left / week | one decimal, bold |
| Games blown | integer, bold |

**Footnote**: "Games blown = losses the best lineup would have won. Every completed week counts,
playoffs included. Worst first.", then the in-progress note and "Updated <time>".

**When ESPN is unavailable**: show cached numbers with "Couldn't reach ESPN. Showing numbers as
of <time>.", or "Couldn't reach ESPN. Try again later." with nothing cached. Always 200.

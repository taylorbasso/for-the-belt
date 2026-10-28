# Data Model: Historical Records

Nothing is persisted. These are plain Python dataclasses built from ESPN responses and held in
an in-memory cache (see research.md §2).

## ManagerSeason

One manager's regular-season results for one season, built from one `teams[]` entry in
ESPN's `mTeam` view.

| Field | Type | Source |
|-------|------|--------|
| `year` | int | the requested season |
| `member_id` | str | `team.primaryOwner`; the team name if the owner isn't in `members` |
| `name` | str | the member's `firstName lastName`; the team name as a fallback |
| `wins` / `losses` / `ties` | int | `team.record.overall` |
| `points_for` / `points_against` | float | `team.record.overall` |
| `final_rank` | int | `team.rankCalculatedFinal` (0 while the season is in progress) |
| `shotguns` | int | completed weeks with the season's lowest score (see below) |

## Season

Everything fetched for one year: the unit the cache stores.

| Field | Type | Notes |
|-------|------|-------|
| `year` | int | |
| `managers` | list[ManagerSeason] | one per team |
| `in_progress` | bool | `latestScoringPeriod <= finalScoringPeriod` |
| `previous_seasons` | list[int] | `status.previousSeasons`; only used on the current season |
| `fetched_at` | datetime (UTC) | when the app got it from ESPN |

## AllTimeRecord

Computed per manager by a pure function over all cached seasons. This is one row on the page.

| Field | Type | Rule |
|-------|------|------|
| `member_id` | str | grouping key (FR-003) |
| `name` | str | name from the manager's most recent season |
| `seasons` | int | count of the manager's ManagerSeasons |
| `wins` / `losses` / `ties` | int | sums |
| `win_pct` | float | `(wins + ties/2) / games`, or 0 if no games (FR-005) |
| `points_for` / `points_against` | float | sums |
| `titles` | int | count of seasons with `final_rank == 1` (FR-006) |
| `shotguns` | int | sum of the manager's season shotguns (FR-012) |

**Ordering (FR-007)**: by `win_pct` descending, then `points_for` descending.

## Shotguns

Computed per season from the `mMatchupScore` view's `schedule[].home/away.pointsByScoringPeriod`
(per NFL week, since playoff matchups span two weeks). A week counts once it's before
`status.latestScoringPeriod`. In each week, every team tied for the lowest score gets one.

## Cache rules

- Completed seasons, once fetched, are never re-fetched while the process lives.
- The current season is re-fetched when its `fetched_at` is more than 15 minutes old.
- A failed fetch leaves the cache unchanged and marks the page as "ESPN unavailable"
  (FR-010).

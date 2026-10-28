# Data Model: Bench Tab

Nothing is persisted. It builds on [001 data-model](../001-historical-records/data-model.md).

## ManagerSeason (extended)

Gains `team_id: int`, the ESPN team id, so lineup data (keyed by team) can be matched to a member.

## Lineups (one per season; cached in `espn.py`)

| Field | Type | Notes |
|-------|------|-------|
| `year` | int | |
| `slot_counts` | dict[int, int] | starting slots only (no bench 20 / IR 21) |
| `team_weeks` | list[TeamWeek] | every completed week × team |
| `matchups` | list[Matchup] | completed matchups with a winner |
| `fetched_at` | datetime (UTC) | |

**TeamWeek**: `week: int`, `team_id: int`, `players: list[Player]`.

**Player**: `name: str`, `slot: int` (where they were put), `points: float`,
`eligible: frozenset[int]`.

**Matchup**: `weeks: list[int]`, `winner_id: int`, `loser_id: int`, `winner_points: float`.
Ties and byes are left out.

## Computed in `bench.py`

**best_lineup(players, slot_counts) → (points, chosen players)**: greedy, most restrictive slot
first, IR excluded (research.md §3).

**ManagerWeek**: `year`, `week`, `member_id`, `started`, `best`, and `swap`
(`(bench Player, starter Player)` or `None`).

**BenchRecord**: one row on the page, grouped by `member_id` over the selected seasons.

| Field | Rule |
|-------|------|
| `name` | from the manager's most recent selected season |
| `started` / `best` | sums of weekly points |
| `weeks` | team-weeks counted |
| `lineup_pct` | `started / best` (1.0 when `best` is 0) |
| `bench_per_week` | `(best − started) / weeks` |
| `lineup_losses` | count of Matchups lost where the sum of `best` over the matchup's weeks > `winner_points` |
| `worst` | the ManagerWeek with the largest `best − started`, or `None` if it's 0 |

**Ordering (FR-007)**: `lineup_pct` descending.

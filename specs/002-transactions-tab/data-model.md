# Data Model: Transactions Tab

Nothing is persisted. It builds on feature 001's model ([001 data-model](../001-historical-records/data-model.md)).

## ManagerSeason (extended)

Five new integer fields, read from `team.transactionCounter` in the `mTeam` view (see
research.md §1):

| Field | Source |
|-------|--------|
| `pickups` | `acquisitions` |
| `drops` | `drops` |
| `trades` | `trades` |
| `lineup_moves` | `moveToActive` |
| `ir_moves` | `moveToIR` |

A missing field reads as 0.

## ManagerMoves

One row on the Transactions page. It's computed by a pure function over the selected seasons,
grouped by `member_id` like Records' `AllTimeRecord`.

| Field | Rule |
|-------|------|
| `member_id` | grouping key (FR-005) |
| `name` | name from the manager's most recent selected season |
| `pickups` / `drops` / `trades` / `lineup_moves` / `ir_moves` | sums |

**Ordering (FR-006)**: `pickups` descending, then `name`.

## Season selection (shared)

`select_seasons(seasons, choice)` returns:
- `years`: every season, newest first, as strings
- `selected`: the chosen year, or `"all"`
- `shown`: the seasons to aggregate

When `choice` is missing or isn't a known year (and isn't `"all"`), `selected` is the current
season. This is the same rule as Records today.

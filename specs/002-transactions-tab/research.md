# Research: Transactions Tab

All findings were checked against the real league on 2026-10-27.

## 1. Where the counts come from: `teams[].transactionCounter` in the `mTeam` view

- **Decision**: Read five fields from each team's `transactionCounter`, which is already in the
  `mTeam` response `espn.fetch_season()` requests:

  | Column | Field |
  |--------|-------|
  | Pickups | `acquisitions` |
  | Drops | `drops` |
  | Trades | `trades` |
  | Lineup | `moveToActive` |
  | IR | `moveToIR` |

- **Rationale**: Zero new requests. The counters exist for every season from 2022 on. They're
  ESPN's own season totals, playoffs included (FR-004), and SC-001 is defined against exactly
  these totals. Examples: in 2025 Cody had 60 pickups and 63 drops, and Anthony had 197 lineup
  moves.
- **Alternatives considered**: Count the transaction log (`mTransactions2`, one request per
  week) instead. A cross-check on 2026 didn't reconcile cleanly with the counters:
  - Standalone drops are logged as `ROSTER` transactions.
  - Trades appear as `TRADE_UPHOLD`/`TRADE_VETO`/`TRADE_DECLINE` records that need
    interpreting.
  - Failed claims need filtering.

  It would cost about 18 requests per season for no benefit, since the tab shows counts only.

## 2. Other counter fields: not shown

- **Decision**: Ignore `acquisitionBudgetSpent`, `paid`, `misc`, `teamCharges` and
  `matchupAcquisitionTotals`.
- **Rationale**: The league uses standard waivers with no FAAB budget
  (`isUsingAcquisitionBudget: false`), so budget spent is always 0. `paid` and `misc` are 0
  everywhere. Per-matchup totals are more detail than the spec asks for.

## 3. Sharing the season dropdown with Records

- **Decision**: Move the selection logic from `records.index` into `espn.select_seasons(seasons,
  choice)`, which returns the year list, the selected value and the seasons to show. Move the
  dropdown `<form>` into `templates/_season_picker.html`, included by both tabs.
- **Rationale**: Two tabs need the same behavior (Principle V). Keeping one copy keeps the
  default (current season) and the fallback for unknown years identical.
- **Alternatives considered**: Copy the ten lines into the new route. That works, but the two
  copies would drift.

## 4. Ranking

- **Decision**: Sort by pickups descending, then name.
- **Rationale**: FR-006. Name makes the order stable when counts tie.

## 5. Phone width

- **Decision**: Short column headers: Manager, Pickups, Drops, Trades, Lineup, IR. Use the same
  table styles as Records (`table.records`).
- **Rationale**: Six columns of small integers are narrower than Records' eight. Confirm
  visually at 375px during implementation.

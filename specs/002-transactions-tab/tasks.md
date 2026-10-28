# Tasks: Transactions Tab

**Input**: Design documents from `/specs/002-transactions-tab/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/web-routes.md, quickstart.md

**Tests**: One small test file for the all-time summing and the route's season selection, as
the plan lists. No other tests.

**Organization**: The spec has a single user story (US1). Foundational work extends the shared
ESPN data and moves the season dropdown into shared pieces, so Records keeps working at each step.
There's no Setup phase: the app skeleton, tooling and infrastructure already exist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)

---

## Phase 1: Foundational (Shared Pieces)

**Purpose**: Give every season the move counts, and share the season dropdown between tabs.

- [X] T001 In `src/belt/espn.py`, add five `int` fields to the frozen `ManagerSeason` dataclass,
  after `shotguns`: `pickups`, `drops`, `trades`, `lineup_moves`, `ir_moves`. Give each a trailing
  comment like the existing fields. In `fetch_season()`, read them from
  `team.get("transactionCounter", {})`: `acquisitions`, `drops`, `trades`, `moveToActive`,
  `moveToIR`, each defaulting to 0 (data-model.md). The request's views stay
  `["mTeam", "mMatchupScore"]`.
- [X] T002 In `src/belt/espn.py`, add `select_seasons(seasons, choice) -> tuple[list[str], str,
  list[Season]]` returning `(years, selected, shown)`. Move the logic out of `records.index` in
  `src/belt/records.py` unchanged:
  - `years`: season years as strings, newest first.
  - `selected`: `"all"`, or a known year; anything else falls back to `years[0]` (or `"all"`
    when there are no seasons).
  - `shown`: all seasons for `"all"`, otherwise the one selected season.

  Give it a one-line docstring.
- [X] T003 Update `records.index` in `src/belt/records.py` to call
  `espn.select_seasons(seasons, request.args.get("season"))`. Render the same template
  variables as before, so Records behaves exactly as it does now.
- [X] T004 [P] Create `src/belt/templates/_season_picker.html` containing the
  `<form class="season-picker">` block, moved as-is from `src/belt/templates/records.html`. It
  uses `years` and `selected`. Replace the block in `records.html` with
  `{% include "_season_picker.html" %}`.
- [X] T005 [P] Update the `manager()` helper in `tests/test_records.py` to pass the five new
  `ManagerSeason` fields (keyword args defaulting to 0), so the existing tests still build
  seasons.

**Checkpoint**: `./scripts/check.sh` passes. After `./scripts/dev-server.sh restart`,
`/records` looks and behaves the same as before: default 2026, `?season=2024`, `?season=all`.

---

## Phase 2: User Story 1 - See who works the waiver wire (Priority: P1) 🎯 MVP

**Goal**: A public Transactions tab with pickups, drops, trades, lineup moves and IR moves per
manager, for one season or all time.

**Independent Test**: Open `/transactions?season=2025` and compare it with the 2025 baseline
table in quickstart.md. All time has 9 rows with no duplicates.

- [X] T006 [US1] Create `src/belt/transactions.py`, mirroring `src/belt/records.py`'s style:
  - Module docstring.
  - `@dataclass ManagerMoves` with `member_id`, `name`, and the five counts defaulting to 0.
  - `all_moves(seasons: list[Season]) -> list[ManagerMoves]`: walk seasons oldest first,
    group by `member_id`, take the name from the latest season, and sum the five counts. Sort
    by `pickups` descending, then `name`.
  - `bp = Blueprint("transactions", __name__)` with `GET /transactions`. Call
    `espn.get_seasons()` and `espn.select_seasons(...)`. Render `transactions.html` with
    `rows`, `years`, `selected`, `in_progress`, `current`, `updated` (in `LEAGUE_TZ`, imported
    from `belt.records`) and `espn_error`, computed the same way as `records.index`.
- [X] T007 [P] [US1] Create `src/belt/templates/transactions.html`, extending `layout.html`
  with title "Transactions", following `records.html`:
  - The same ESPN-error notices, with "records" replaced by "counts".
  - `{% include "_season_picker.html" %}`.
  - A `table.records` with columns Manager, Pickups, Drops, Trades, Lineup, IR (the `name`
    class on the Manager column).
  - The footnote from contracts/web-routes.md: "Pickups include waiver claims and free agents.
    A trade counts once for each manager in it. Lineup = players moved into the starting
    lineup." Then "{year} season in progress." when `in_progress`, then "Updated {time}."
- [X] T008 [US1] Register `belt.transactions.bp` in `create_app()` in `src/belt/app.py`, next to
  the records blueprint.
- [X] T009 [P] [US1] Add a second tab link "Transactions" to `src/belt/templates/layout.html`,
  active when `request.endpoint == 'transactions.index'`, matching the Records link.
- [X] T010 [P] [US1] Create `tests/test_transactions.py`, following `tests/test_records.py`'s
  helpers:
  - `all_moves` sums counts across seasons under one member, with the latest name.
  - It ranks by pickups.
  - A route test that monkeypatches `espn.get_seasons`: the default is the current season,
    `?season=<past year>` shows that year, and `?season=all` sums both.
- [X] T011 [US1] Run `./scripts/check.sh` and restart the dev server. Check quickstart.md
  steps 1–5 against `http://127.0.0.1:5002/transactions`, including the 2025 baseline table.

**Checkpoint**: The Transactions tab works locally and matches the baseline.

---

## Phase 3: Polish & Ship

- [X] T012 Check both tabs at a 375px-wide viewport, light and dark, with no sideways scroll
  (quickstart step 6). Adjust `src/belt/static/style.css` only if the six-column table needs it.
- [X] T013 [P] Add `src/belt/transactions.py` to "Where things are" in `CLAUDE.md`, and mention
  that `espn.py` also holds the shared season selection.
- [X] T014 Deploy with `uv run deploy/deploy.py`, then repeat quickstart steps 1–4 against
  https://fantasy.taylorbasso.dev/transactions.

---

## Dependencies & Execution Order

- **Foundational (T001–T005)**: T001 and T002 both edit `espn.py`, so do them in order.
  - T003 needs T002.
  - T004 and T005 can run any time in this phase.
- **US1 (T006–T011)**:
  - T006 needs T001 and T002.
  - T007, T009 and T010 can run in parallel with T006.
  - T008 needs T006. T011 comes last.
- **Polish (T012–T014)**: after T011. T013 can run any time. T014 comes last.

## Parallel Example: User Story 1

```text
After T001–T002:  T006 (transactions.py)  ‖  T007 (transactions.html)  ‖  T009 (layout.html)  ‖  T010 (tests)
Then:             T008 (app.py) → T011 (verify)
```

## Implementation Strategy

1. **Foundational**: Records unchanged, with the shared pieces in place.
2. **MVP**: US1, working locally and matching the 2025 baseline.
3. **Ship**: Phone check and deploy.

# Tasks: Bench Tab

**Input**: Design documents from `/specs/003-bench-tab/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/web-routes.md, quickstart.md

**Tests**: `tests/test_bench.py` covers the best-lineup math, costliest swap, lineup losses and
summing, which the plan calls "easy to get wrong". No other tests.

**Organization**: One user story (US1). Foundational work adds the per-week lineup fetch and cache
to `espn.py`. There's no Setup phase: the app, tooling and infrastructure already exist.

**Reference**: research.md has the exact ESPN fields and slot ids. The throwaway prototype that
validated them isn't in the repo; build from research.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)

---

## Phase 1: Foundational (Per-Week Lineup Data)

**Purpose**: Get every completed week's rosters from ESPN, cached like seasons.

- [X] T001 In `src/belt/espn.py`, add `team_id: int` to `ManagerSeason`, right after `year`,
  with the matching `team_id=team["id"]` in `fetch_season()`. Update the `manager()` helper in
  `tests/test_records.py` to take a `team_id=0` keyword and pass it through. Run
  `./scripts/check.sh`.
- [X] T002 In `src/belt/espn.py`, add frozen dataclasses from data-model.md:
  - `Player(name: str, slot: int, points: float, eligible: frozenset[int])`
  - `TeamWeek(week: int, team_id: int, players: list[Player])`
  - `Matchup(weeks: list[int], winner_id: int, loser_id: int, winner_points: float)`
  - `Lineups(year: int, slot_counts: dict[int, int], team_weeks: list[TeamWeek], matchups:
    list[Matchup], fetched_at: datetime)`
- [X] T003 In `src/belt/espn.py`, add `fetch_lineups(season: Season) -> Lineups`, per research.md
  §1, §2, §5 and §6:
  - **Weeks**: 1 through the last completed week. Store `last_completed_week` on `Season` (a new
    field, set in `fetch_season()` as `min(latestScoringPeriod - 1, finalScoringPeriod)`), and
    read it here.
  - **Requests**: fetch weeks in parallel with `ThreadPoolExecutor(max_workers=8)`. Each week
    builds its own `League(..., fetch_league=False)` and calls
    `espn_request.league_get(params={"view": ["mMatchup"], "scoringPeriodId": w})` (mMatchupScore was
    dropped after deploy; see research.md §1).
    Week 1's request also includes `"mSettings"`.
  - **`slot_counts`**: from week 1's `settings.rosterSettings.lineupSlotCounts`, as ints. Drop
    20 and 21 and any zero counts.
  - **`team_weeks`**: for each schedule side that has `rosterForCurrentScoringPeriod` and
    `str(w)` in its `pointsByScoringPeriod`, build one `TeamWeek`. For each entry:
    - `name`: `playerPoolEntry.player.fullName`
    - `slot`: `lineupSlotId`
    - `points`: `playerPoolEntry.appliedStatTotal`
    - `eligible`: `frozenset(player.eligibleSlots)`
  - **`matchups`**: from the last week's response `schedule`, keep matchups that have both
    `home` and `away` and a `winner` of `"HOME"` or `"AWAY"`. Only keep those whose weeks (the
    keys of `pointsByScoringPeriod`) are all ≤ the last completed week. `winner_points` is the
    winner's `totalPoints`.
- [X] T004 In `src/belt/espn.py`, add `_lineup_cache: dict[int, Lineups]` and
  `get_lineups(seasons: list[Season]) -> tuple[list[Lineups], bool]`:
  - For each given season, fetch it if it's missing. Re-fetch it if it's in progress and the
    cached copy is older than `CURRENT_SEASON_MAX_AGE`.
  - On exception, log only `type(exc).__name__` (same as `get_seasons()`) and set the error
    flag.
  - Return the cached `Lineups` for those seasons, in order, and the flag.

**Checkpoint**: In a Python shell with `.env` loaded, `espn.get_lineups(espn.get_seasons()[0])`
returns 5 `Lineups`. 2025 has 144 team-weeks and `slot_counts` has `{23: 2}`; 2024 has `{23: 1}`.

---

## Phase 2: User Story 1 - Find out who can't set a lineup (Priority: P1) 🎯 MVP

**Goal**: A public Bench tab with Lineup %, Bench/wk, lineup losses and worst week per manager,
for one season or all time.

**Independent Test**: quickstart.md steps 1–4, including the 2024 week 5 Burrow/Purdy line.

- [X] T005 [US1] Create `src/belt/bench.py` with the pure logic, per data-model.md and research.md
  §3–§5. Mirror `records.py`'s style (module docstring, `from __future__ import annotations`).
  - `best_lineup(players, slot_counts) -> tuple[float, list[Player]]`:
    - Candidates are players with `slot != 21`.
    - Build the slot list from `slot_counts` and sort it by how many candidates are eligible,
      fewest first.
    - For each slot, take the highest-scoring remaining eligible candidate. Skip the slot if
      there's none.
  - `costliest_swap(players, chosen) -> tuple[Player, Player] | None`: of every pair of a
    benched player (`slot == 20`) in `chosen` and a starter (`slot not in (20, 21)`) not in
    `chosen` whose `slot` is in the bench player's `eligible`, return the pair with the biggest
    point gap, or `None` if there's no pair. (Revised during implementation; see spec FR-004a.)
  - `@dataclass ManagerWeek`: `year`, `week`, `member_id`, `started`, `best`, `swap`, plus a
    `left` property (`best - started`).
  - `manager_weeks(season: Season, lineups: Lineups) -> list[ManagerWeek]`:
    - Map `team_id` to `member_id` via `season.managers`.
    - `started` is the sum of points for slots not 20 or 21.
  - `lineup_losses(season, lineups, weeks: list[ManagerWeek]) -> dict[str, int]`, by member_id:
    for each Matchup, add the loser's `best` over `matchup.weeks`. If that's more than
    `winner_points`, it's a lineup loss.
  - `@dataclass BenchRecord`:
    - Fields: `member_id`, `name`, `started`, `best`, `weeks`, `lineup_losses`, and `worst:
      ManagerWeek | None`.
    - Properties: `lineup_pct` (`started / best`, 1.0 if `best` is 0) and `bench_per_week`.
  - `bench_records(seasons, lineups) -> list[BenchRecord]`:
    - Walk the pairs oldest first, grouping by member_id. Take the name from the latest season.
    - `worst` is the week with the largest `left`; keep it `None` while `left` is 0.
    - Sort by `lineup_pct` descending.
- [X] T006 [US1] Add the `/bench` blueprint to `src/belt/bench.py`:
  - Call `espn.get_seasons()`, then `espn.select_seasons(...)`, then
    `espn.get_lineups(shown)`.
  - `espn_error` is either flag. Render `bench.html` with the same variables as the
    Transactions route.
  - Pair each shown season with its `Lineups` by year, skipping seasons whose lineups aren't
    cached (only possible after an ESPN failure).
- [X] T007 [P] [US1] Create `src/belt/templates/bench.html`, following
  `src/belt/templates/transactions.html` and contracts/web-routes.md:
  - The notices, with the word "numbers".
  - The season picker include.
  - A `table.records` with columns Manager, Lineup %, Bench/wk and L. losses.
  - In the name cell, the name, then `<div class="sub">`:
    - With a worst week: `Wk {week} '{yy}: −{left:.1f}`, plus
      ` · benched {bench.name} ({bench.points:.1f}) for {starter.name} ({starter.points:.1f})`
      when there's a swap.
    - Otherwise a `–`.
  - The footnote text from the contract.
- [X] T008 [P] [US1] Add `.sub` to `src/belt/static/style.css`: muted color, `font-size: 0.75rem`,
  normal weight, and a little top margin. It must wrap inside the name cell.
- [X] T009 [US1] Register `belt.bench.bp` in `create_app()` in `src/belt/app.py`, and add a
  "Bench" tab link to `src/belt/templates/layout.html`, matching the existing two.
- [X] T010 [P] [US1] Create `tests/test_bench.py`:
  - **`best_lineup` basics**: a bench WR (25) beats a starting WR (6), so `left` is 19
    (spec acceptance 2).
  - **No bench edge**: no bench player beats an eligible starter, so `left` is 0
    (acceptance 1).
  - **FLEX**: a bench RB fills FLEX over a starting TE in FLEX.
  - **IR**: IR players are never chosen.
  - **`costliest_swap`**: pairs only by slot eligibility (a benched QB doesn't replace a WR).
  - **Lineup losses**: a two-week matchup sums both weeks' best (acceptance 3), and a loss the
    best lineup still loses isn't counted.
  - **`bench_records`**: groups by member across seasons and picks the worst week.
- [X] T011 [US1] Run `./scripts/check.sh`, restart the dev server, and check quickstart.md
  steps 1–5 against `http://127.0.0.1:5002/bench`.

**Checkpoint**: The Bench tab works locally and shows the 2024 week 5 baseline line.

---

## Phase 3: Polish & Ship

- [X] T012 Check all three tabs at a 375px-wide viewport, light and dark, with no sideways scroll
  (quickstart step 6). Adjust `src/belt/static/style.css` only if needed.
- [X] T013 [P] Add `src/belt/bench.py` to "Where things are" in `CLAUDE.md`, and note that
  `espn.py` also fetches per-week lineups.
- [X] T014 Deploy with `uv run deploy/deploy.py`, then repeat quickstart steps 1, 3 and 4 on
  https://fantasy.taylorbasso.dev/bench.

---

## Dependencies & Execution Order

- **Foundational**: T001 → T002 → T003 → T004. They're sequential because they all touch
  `espn.py`.
- **US1**:
  - T005 needs T002.
  - T007, T008 and T010 can run in parallel with T005. T010 is written against T005's
    signatures.
  - T006 needs T004 and T005. T009 needs T006. T011 comes last.
- **Polish**: after T011. T013 can run any time. T014 comes last.

## Parallel Example: User Story 1

```text
After T002:  T005 (bench.py logic)  ‖  T007 (bench.html)  ‖  T008 (style.css)  ‖  T010 (tests)
Then:        T006 (route) → T009 (app.py + layout) → T011 (verify)
```

## Implementation Strategy

1. **Foundational**: lineup data fetched and cached; the other tabs unchanged.
2. **MVP**: US1, working locally and matching the 2024 week 5 baseline.
3. **Ship**: Phone check and deploy.

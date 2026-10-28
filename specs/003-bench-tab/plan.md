# Implementation Plan: Bench Tab

**Branch**: `003-bench-tab` (spec directory; work happens on `master`) | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-bench-tab/spec.md`

## Summary

A public Bench tab that judges each manager's lineups against the best lineup they could have
set in hindsight. It shows Lineup %, points left on the bench per week, lineup losses, and
their worst week with the swap that cost the most. It has the same season dropdown as the
other tabs.

This tab needs per-week rosters, which the app doesn't fetch yet: one ESPN request per week,
about 85 for the league's history. They're fetched in parallel, 8 at a time, only for the
seasons the page is showing. Each season is cached in memory like the others. A prototype
against the real league reconciled all 596 team-weeks with ESPN's scores, and loaded every
season in about 6s. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Flask, gunicorn, espn-api (unchanged). `concurrent.futures` from the
standard library for parallel fetches.

**Storage**: None. A second in-memory cache in `espn.py`, keyed by season.

**Testing**: pytest: the best-lineup math, costliest swap, lineup losses and summing. This is
the "easy to get wrong" logic the constitution asks to test.

**Target Platform**: Same container and ECS service. No infrastructure changes.

**Project Type**: Web app, server-rendered

**Performance Goals**:
- Default view (current season): about 8 requests in parallel, under 1s cold.
- All time cold: about 6s, once per process. Within gunicorn's 30s worker timeout.
- Warm: instant (SC-004).

**Constraints**:
- 375px width.
- ESPN read-only.
- Don't hammer ESPN: completed seasons are fetched once per process, and the current season
  at most every 15 minutes.

**Scale/Scope**: about 600 team-weeks, about 16 players each. One page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. KISS | One module with a greedy best-lineup function, plus one fetch function and cache. No background jobs, no DB, no warm-up thread: the first All time view after a deploy just waits about 6s. | ✅ |
| II. ESPN read-only and unofficial | Reads only. A failed fetch falls back to cached data plus a notice, like the other tabs. | ✅ |
| III. One small app | No new dependencies or infrastructure; the thread pool is standard library. | ✅ |
| IV. Phone-first | Four columns. The worst week goes on a second line under the name. Public like the other tabs (FR-011). | ✅ |
| V. Features are tabs | Own module, blueprint, template and tab. Reuses the shared season picker and season list. | ✅ |
| Secrets & data | No new secrets or stored data. | ✅ |

**Post-design re-check (after Phase 1)**: still passes. The design added nothing beyond the
table above.

## Project Structure

### Documentation (this feature)

```text
specs/003-bench-tab/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/web-routes.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/belt/
├── app.py               # register the bench blueprint
├── espn.py              # ManagerSeason gains team_id; new fetch_lineups(year) and get_lineups(seasons)
│                        # with their own cache (completed seasons once, current every 15 min)
├── bench.py             # NEW: best_lineup(), per-week results, lineup losses, BenchRecord rows, /bench blueprint
├── templates/
│   ├── layout.html      # third tab link
│   └── bench.html       # NEW
└── static/style.css     # small muted second line for the worst week
tests/
├── test_records.py      # manager() helper gains team_id
└── test_bench.py        # NEW
```

`CLAUDE.md` "Where things are" gains `bench.py`.

**Structure Decision**: The same one-module-per-tab layout. ESPN fetching and caching stay in
`espn.py`. All the lineup math lives in `bench.py` as pure functions over plain data, so it's
easy to test without ESPN.

## Complexity Tracking

| Addition | Why needed | Simpler alternative rejected because |
|----------|------------|--------------------------------------|
| Parallel fetch (8 threads) | About 85 sequential requests take about 25s cold, close to gunicorn's 30s timeout. | Sequential risks timeouts. A background warm-up thread or a DB is more moving parts than a thread pool inside one function. |

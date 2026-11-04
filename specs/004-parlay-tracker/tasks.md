# Tasks: Parlay Tracker

**Input**: Design documents from `/specs/004-parlay-tracker/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/web-routes.md, quickstart.md

**Tests**: `tests/test_parlays.py` covers the parlay result, records, implied odds, parlay-killer
counts and ranking, which the plan calls "easy to get wrong". No other tests.

**Organization**: US1 (member stats) and US3 (recording a week) are P1; US2 (week list) is P2.
US3 needs no app code beyond the data file and a CLAUDE.md routine. There's no Setup phase: the
app, tooling and infrastructure already exist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Foundational (Data File and Loading)

**Purpose**: The stored file and the code that reads it. Every story needs it.

- [X] T001 Create `src/belt/data/parlays.json` containing `{"parlays": []}` (data-model.md).
- [X] T002 Create `src/belt/parlays.py` with a module docstring, `bp = Blueprint("parlays",
  __name__)`, frozen dataclasses `Leg(member: str, pick: str, odds: int | None, result: str |
  None)` and `Parlay(season: int, week: int, lsp: str, category: str, payout: float | None, legs:
  list[Leg])`, and `load_parlays(path: Path = PARLAYS) -> list[Parlay]` where `PARLAYS =
  Path(__file__).parent / "data" / "parlays.json"`. Return parlays newest first (season, then
  week, descending). No validation.

**Checkpoint**: `load_parlays()` returns `[]`.

---

## Phase 2: User Story 1 - Find out who keeps busting the parlay (Priority: P1) 🎯 MVP

**Goal**: One row per member with record, hit rate, expected hit rate and parlay-killer count,
worst first.

**Independent Test**: Load sample parlays and compare each member's numbers with a hand count
(spec US1 scenarios).

- [X] T003 [US1] In `src/belt/parlays.py`, add:
  - `result(p: Parlay) -> str`: `"busted"` if any leg is `"L"`, `"hit"` if every leg is `"W"`,
    else `"pending"` (research §5).
  - `sole_loser(p: Parlay) -> str | None`: the member whose leg is the only `"L"`, when every leg
    is graded; else None.
  - `implied(odds: int) -> float`: −X → X/(X+100), +X → 100/(X+100) (research §4).
  - `@dataclass MemberStats(name, wins=0, losses=0, kills=0, implied_sum=0.0, implied_n=0)` with
    properties `hit_rate` (wins/(wins+losses), None if 0 graded) and `expected_rate`
    (implied_sum/implied_n, None if 0).
  - `member_stats(parlays) -> list[MemberStats]`: one per member seen in any leg (including
    ungraded). Only graded legs count toward wins, losses and implied odds; legs with null odds
    are left out of implied odds only. Kills from `sole_loser`. Sorted per research §6: kills
    descending, then hit rate ascending with None last, then name.
- [X] T004 [P] [US1] Write `tests/test_parlays.py` covering spec US1 scenarios 1–5:
  3-1 record and 75% hit rate; sole loser gets the kill and nobody else; two losses give no kill;
  −200 and +100 average to 58.3%; ungraded member shows 0-0 with None rates and sorts last. Also:
  `result()` for hit, busted (one L with others null) and pending; no kill while any leg is null;
  null odds skipped in expected rate but counted in the record. Build parlays directly with the
  dataclasses.
- [X] T005 [US1] In `src/belt/parlays.py`, add the `/parlays` route: load parlays, build
  `stats`, a summary (settled count, hits, total payout of hits with payouts), and render
  `parlays.html`. Register the blueprint in `src/belt/app.py`.
- [X] T006 [US1] Create `src/belt/templates/parlays.html` extending `layout.html`: heading,
  intro and summary line, the stats table, footnote, and the empty state, per
  contracts/web-routes.md. Reuse the `records` table class, `page-title`, `intro`, `footnote` and
  `big` styles.
- [X] T007 [US1] Add the Parlays link to the tab bar in `src/belt/templates/layout.html`, after
  Bench.

**Checkpoint**: `/parlays` shows the empty state; with a sample file it shows the table.

---

## Phase 3: User Story 2 - See each week's parlay (Priority: P2)

**Goal**: Every recorded week, newest first, with LSP, category, legs and result.

**Independent Test**: Put one sample week in the file and check the tab shows it exactly as
entered (spec US2 scenarios).

- [X] T008 [US2] In `src/belt/parlays.py`'s route, pass each parlay with its `result()` and
  `sole_loser()`, and whether more than one season is recorded.
- [X] T009 [US2] In `src/belt/templates/parlays.html`, add the week blocks below the table per
  contracts/web-routes.md: heading with week (and season when needed) and result, the LSP's
  category, and one row per leg with name, pick below it, signed odds (`+240`, `−150`, blank),
  and ✅/❌/pending, with "killed it" on the sole loser.
- [X] T010 [P] [US2] In `src/belt/static/style.css`, add minimal styles for the week blocks
  (heading spacing, result label colors using existing variables). Keep it under 30 lines.

**Checkpoint**: quickstart steps 3 and 4 pass with a sample file.

---

## Phase 4: User Story 3 - Record a week (Priority: P1)

**Goal**: Any future Claude session knows how to record and grade a week.

**Independent Test**: A fresh session, given only CLAUDE.md and a pasted slip, adds a correct
entry.

- [X] T011 [US3] In `CLAUDE.md`, add `src/belt/parlays.py` and `src/belt/data/parlays.json` to
  "Where things are", and a short "Recording a parlay" section: the file's shape (link
  data-model.md), member names exactly as the other tabs show them (list the eight), `week` is
  the NFL week of the games, results null until graded, payout only when it hit, run
  `./scripts/check.sh`, then commit and deploy.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T012 Run `./scripts/check.sh`; all tests pass.
- [X] T013 Run quickstart.md "Validate locally" with a temporary sample file, including a
  375px-wide check, then restore `src/belt/data/parlays.json` to `{"parlays": []}`.
- [X] T014 Update `.specify/memory/constitution.md` and research notes that say Postgres
  "arrives with the bet tracker" only if they'd now mislead. (Constitution: it says nothing about
  Postgres timing, so likely no change. CLAUDE.md's `records.py` line does; update it to "arrives
  with the admin login, if built".)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → Phase 3. Phase 4 can run any time after Phase 1.
- T004 (tests) can be written alongside T003.
- T010 (CSS) is independent of T008–T009.

## Parallel Example

```text
T003 parlays.py logic   ‖  T004 tests/test_parlays.py
T009 template weeks     ‖  T010 style.css
```

## Implementation Strategy

MVP is Phases 1–2 plus T011: the stats table and the recording routine. Phase 3 adds the
receipts. It's small enough to do all of it in one pass.

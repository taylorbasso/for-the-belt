# Implementation Plan: Parlay Tracker

**Branch**: `004-parlay-tracker` (spec directory; work happens on `master`) | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-parlay-tracker/spec.md`

## Summary

A public Parlays tab for the weekly loser parlay. Up top, one row per member with their leg
record, hit rate, the hit rate their odds implied, and how many parlays they killed alone. Below
that, every recorded week, newest first, with the LSP, category, legs and result.

The data is one hand-edited JSON file in the repo, `src/belt/data/parlays.json`, the same way
`past_seasons.json` works. The LM records and grades each week by asking Claude in a session,
then commits and deploys. No database, logins or entry form: those wait for the admin login,
which is undecided. The tab reads nothing from ESPN. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Flask (unchanged). `json` from the standard library.

**Storage**: `src/belt/data/parlays.json`, read on each request (it's a few KB). Already packaged
by the `data/*` package-data rule and copied into the image with `src/`.

**Testing**: pytest: parlay result, records, implied odds, parlay-killer counts and ranking. This
is the "easy to get wrong" logic the constitution asks to test.

**Target Platform**: Same container and ECS service. No infrastructure changes.

**Project Type**: Web app, server-rendered

**Performance Goals**: Instant. One small file read, no network (SC-003).

**Constraints**: 375px width. No ESPN calls.

**Scale/Scope**: About 18 parlays and 150 legs a season. One page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. KISS | One data file, one module of pure functions, one template. No DB, auth or form until they're actually needed. No handling for ties, missing legs, pushes or voids. | ✅ |
| II. ESPN read-only and unofficial | Doesn't touch ESPN at all, so it works when ESPN is down. | ✅ |
| III. One small app | No new dependencies or infrastructure. But the parlays are data the app owns, and III says that lives in Postgres. They live in a repo file instead: see Complexity Tracking. | ⚠️ justified |
| IV. Phone-first | Stats table has five narrow columns. Each leg is one row with the member's name above the pick. Public like the other tabs (FR-012). Logins aren't needed: there's no member input. | ✅ |
| V. Features are tabs | Own module, blueprint, template and tab. Shares nothing with the other tabs but the layout and CSS. | ✅ |
| Secrets & data | No secrets. The file stores names, picks, odds and results: feature data. Payouts are recorded, not handled; money stays in the betting app. | ✅ |

The constitution and earlier plans expected Postgres to "arrive with the bet tracker". It
doesn't yet: with the LM as the only writer and Claude doing the writing, a file does the job.
Postgres arrives with the admin login, if that's built.

**Post-design re-check (after Phase 1)**: still passes. The design added nothing beyond the
table above.

## Project Structure

### Documentation (this feature)

```text
specs/004-parlay-tracker/
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
├── app.py               # register the parlays blueprint
├── parlays.py           # NEW: load the file, parlay result, member stats, /parlays blueprint
├── data/parlays.json    # NEW: {"parlays": []}, filled in week by week
├── templates/
│   ├── layout.html      # fourth tab link
│   └── parlays.html     # NEW
└── static/style.css     # small additions for the week blocks
tests/
└── test_parlays.py      # NEW
```

`CLAUDE.md` gains `parlays.py` under "Where things are", and a short "Recording a parlay"
section so any future session knows the weekly routine.

**Structure Decision**: The same one-module-per-tab layout. All the math lives in `parlays.py`
as pure functions over plain data, so it's easy to test.

## Complexity Tracking

| Departure | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| App-owned data (parlays) in `src/belt/data/parlays.json`, not Postgres (Principle III) | Nothing writes from the web yet: the LM records weeks through Claude. A file needs no database, credentials, schema or auth, and git history is the audit trail. | Postgres is the heavier option here, not the simpler one. It arrives with the admin login, if that's built, with a one-time import of the file. If the file approach sticks, amend Principle III to allow hand-edited data files. |

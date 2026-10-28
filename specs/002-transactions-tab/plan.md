# Implementation Plan: Transactions Tab

**Branch**: `002-transactions-tab` (spec directory; work happens on `master`) | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-transactions-tab/spec.md`

## Summary

A public Transactions tab showing, per manager, pickups, drops, trades, lineup moves and IR
moves for one season or all time, with the same season dropdown as Records. The counts come from
ESPN's per-team transaction counters, which are already in the `mTeam` response the app fetches
for Records. So there are no new ESPN requests, no new cache, and no database. See
[research.md](research.md).

Two features now need the season dropdown, so its selection logic and markup move into shared
pieces (constitution Principle V: share once two features need the same thing).

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Flask, gunicorn, espn-api (unchanged)

**Storage**: None. Reuses the in-memory season cache from `espn.py`.

**Testing**: pytest: all-time summing and the route's season selection

**Target Platform**: Same container and ECS service as Records. No infrastructure changes.

**Project Type**: Web app, server-rendered

**Performance Goals**: Same as Records (SC-003, 3 seconds on a phone). No extra ESPN requests.

**Constraints**: 375px width with no sideways scrolling, for a name column plus five number
columns. ESPN read-only.

**Scale/Scope**: 8 active managers, 9 all-time, 5 seasons. One page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. KISS | One new module and template. Reads five numbers ESPN already sends. No new requests, cache, DB or config. | ✅ |
| II. ESPN read-only and unofficial | Reads only. Same cached-data fallback as Records. | ✅ |
| III. One small app | No new dependencies or infrastructure. | ✅ |
| IV. Phone-first, logged-in members | Phone-first: ✅. Public like Records (spec FR-009); no member input. | ✅ |
| V. Features are tabs | Own module, blueprint and tab. The season picker becomes shared now that two tabs use it. Removing either tab leaves the other working. | ✅ |
| Secrets & data | No new secrets or stored data. | ✅ |

**Post-design re-check (after Phase 1)**: still passes. The design added nothing beyond the
table above.

## Project Structure

### Documentation (this feature)

```text
specs/002-transactions-tab/
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
├── app.py               # register the transactions blueprint
├── espn.py              # ManagerSeason gains the five move counts from transactionCounter;
│                        # new select_seasons() shared by both tabs
├── records.py           # route uses select_seasons() (behavior unchanged)
├── transactions.py      # NEW: all-time summing of move counts + the /transactions blueprint
├── templates/
│   ├── layout.html      # second tab link
│   ├── _season_picker.html  # NEW: the dropdown form, included by both tabs
│   ├── records.html     # includes the picker partial
│   └── transactions.html    # NEW
└── static/style.css     # only if the table needs it at 375px
tests/
├── test_records.py      # unchanged except the ManagerSeason helper's new fields
└── test_transactions.py # NEW: summing across seasons + season selection
```

`CLAUDE.md` "Where things are" gains `transactions.py`.

**Structure Decision**: Same as Records: one module per tab. The shared pieces are
`select_seasons()` in `espn.py`, next to the seasons it filters, and a Jinja partial for the
dropdown markup.

## Complexity Tracking

No violations. Nothing to justify.

# Implementation Plan: Historical Records

**Branch**: `001-historical-records` (spec directory; work happens on `master`) | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-historical-records/spec.md`

## Summary

A public Records tab showing each manager's all-time regular-season record, win %, points for
and against, and titles across every ESPN season since 2022, grouped by ESPN member. It's the
app's first feature, so it also stands up the app skeleton (Flask, templates, scripts, Docker,
deploy script) and its infrastructure unit in basso-infra. All of it mirrors
`~/code/biweekly-budget`.

The data comes from one light ESPN request per season (about 0.15s each) and is held in an
in-memory cache: completed seasons are fetched once, and the current season is refreshed every
15 minutes. There's no database for this feature. See [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Flask, gunicorn, espn-api

**Storage**: None. An in-memory cache only; Postgres arrives with the bet tracker.

**Testing**: pytest, for the aggregation logic only

**Target Platform**: Linux container (ARM64) on ECS Fargate Spot, behind the shared `basso-apps` ALB

**Project Type**: Web app, server-rendered

**Performance Goals**: Full table on a phone within 3 seconds (SC-003). A cold cache is 5
ESPN requests at about 0.15s each.

**Constraints**: Phone width (375px) with no sideways scrolling. ESPN is read-only and
unofficial (Principle II). Public with no login (FR-011).

**Scale/Scope**: 8 active managers, 9 all-time, 5 seasons. One page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. KISS | One page, one cache dict, no DB, no auth, no scheduler. Edge cases limited to the spec's three. | ✅ |
| II. ESPN read-only and unofficial | Reads only. If ESPN fails, the page shows cached data or a message, never an error page. | ✅ |
| III. One small app | One Flask container on Fargate Spot, on the shared ALB. No new infrastructure types. Dependencies: Flask, gunicorn, espn-api (pytest for dev). | ✅ |
| IV. Phone-first, logged-in members | Phone-first: ✅. Login: not used. The tab is public by the LM's explicit choice (spec FR-011), and the login principle applies to features that take member input. | ✅ |
| V. Features are tabs | Records is its own module and its own tab. The shared layout holds only the tab bar. | ✅ |
| Secrets & data | ESPN cookies come from `.env` locally and SSM in AWS. Never logged or committed. | ✅ |

**Post-design re-check (after Phase 1)**: still passes. The design added nothing beyond the
table above.

## Project Structure

### Documentation (this feature)

```text
specs/001-historical-records/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/web-routes.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml           # setuptools, src/ layout; deps: flask, gunicorn, espn-api; dev: pytest
Dockerfile               # python:3.11-slim, non-root, gunicorn on :8000 (copied from biweekly-budget)
.dockerignore
deploy/deploy.py         # podman build → ECR :latest → force new ECS deployment (copied)
scripts/
├── dev-server.sh        # start|stop|restart|status on 127.0.0.1:5002; loads .env
└── check.sh             # pytest
src/belt/
├── app.py               # create_app(), /healthz, / → /records
├── wsgi.py              # gunicorn entry point
├── espn.py              # fetch one season from ESPN (mTeam), in-memory season cache, current-season rule
├── records.py           # pure aggregation into AllTimeRecord rows + the /records blueprint
├── templates/
│   ├── layout.html      # app title + tab bar
│   └── records.html
└── static/style.css     # phone-first table styles
tests/
└── test_records.py      # aggregation: grouping by member, renamed teams, tie-break, ties as half wins, titles, owner fallback
```

Removed: `scripts/lifetime_records.py`. The Records tab replaces it.

Infrastructure, in the separate repo `~/code/basso-infra`:

```text
basso-root/us-west-2/for-the-belt/
├── main.tf              # ECR, logs, execution role (SSM read), task SG, TG, listener rule (priority 200,
│                        # fantasy.taylorbasso.dev) on the shared basso-apps listener, Route 53 alias,
│                        # ECS cluster + task def (ARM64 256/512) + Fargate Spot service
├── variables.tf         # domain, zone_name, espn_league_id
├── outputs.tf
└── terragrunt.hcl
```

**Structure Decision**: A single Flask package `belt` in the biweekly-budget layout. Each tab is
one module that owns its blueprint and logic; `espn.py` is the one shared module, because the bet
tracker will also need ESPN scores.

## Complexity Tracking

No violations. Nothing to justify.

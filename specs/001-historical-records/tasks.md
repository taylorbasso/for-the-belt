# Tasks: Historical Records

**Input**: Design documents from `/specs/001-historical-records/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/web-routes.md, quickstart.md

**Tests**: One small unit test file for the aggregation logic. The plan and the constitution's
Development Workflow call for it as "logic that's easy to get wrong". No other tests.

**Organization**: The spec has a single user story (US1). Setup and Foundational stand up the
app skeleton, which every later tab reuses. The last phase deploys the app.

**Reference repo**: `~/code/biweekly-budget` (BB). Several tasks say "copy from BB"; adapt
names (`budget` → `belt`, `biweekly-budget` → `for-the-belt`, `BUDGET_` → `BELT_`) and drop
anything for DB, auth, sessions, or mypy.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project packaging and local tooling

- [X] T001 Create `pyproject.toml`, following BB's `pyproject.toml`:
  - setuptools build, project name `for-the-belt`, `requires-python = ">=3.11"`.
  - Dependencies: `flask>=3.0`, `gunicorn>=22.0`, `espn-api`. Optional `dev = ["pytest>=8.0"]`.
  - `[tool.setuptools.packages.find] where = ["src"]`, and package-data
    `belt = ["templates/*", "static/*"]`.
  - `[tool.pytest.ini_options] testpaths = ["tests"]`.
  - No mypy and no deploy extras; `deploy/deploy.py` will use inline script metadata instead.
- [X] T002 [P] Extend `.gitignore` with BB's Python entries: `.venv/`, `*.egg-info/`, `.pytest_cache/`,
  `.dev-server.log`, `.DS_Store`. Keep the existing `.env` and `__pycache__/` lines.
- [X] T003 [P] Create `scripts/dev-server.sh` by copying BB's `scripts/dev-server.sh`. Make it executable.
  - Port env var is `BELT_DEV_PORT` (default 5002).
  - Drop the `BUDGET_ENV`/`PGDATABASE` exports.
  - Before starting, load `.env` with `set -a; source .env; set +a`.
  - Run `flask --app belt.app:create_app run --port "$PORT"`.
- [X] T004 [P] Create `scripts/check.sh`. It activates `.venv` and runs `pytest tests/`, with no
  Postgres check and no mypy. Make it executable.
- [X] T005 [P] Create the `Dockerfile` and `.dockerignore` by copying BB's.
  - The Dockerfile `CMD` is `gunicorn --bind 0.0.0.0:8000 belt.wsgi:app`.
  - Add `.env`, `scripts/`, and `deploy/` to `.dockerignore`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: An app that starts, serves a health check, and has the shared layout and ESPN
module the Records tab needs.

- [X] T006 Create `src/belt/__init__.py` (empty) and `src/belt/app.py`.
  - `create_app()` builds the Flask app with `TEMPLATES_AUTO_RELOAD = True`.
  - It registers the records blueprint (imported from `belt.records`) and adds two routes:
    `GET /healthz` returns `"ok"` and never touches ESPN; `GET /` redirects (302) to
    `url_for("records.index")`.
  - No secret key, sessions, DB, or ProxyFix (research.md §7).
- [X] T007 [P] Create `src/belt/wsgi.py` with `app = create_app()`, as in BB's `wsgi.py`.
- [X] T008 [P] Create `src/belt/templates/layout.html`.
  - Mobile viewport meta, `<title>{% block title %}{% endblock %} · For the Belt</title>`.
  - A header with "For the Belt" and a tab bar containing one tab, "Records" (`/records`),
    marked active.
  - A `{% block content %}`. Link `static/style.css`.
- [X] T009 [P] Create `src/belt/static/style.css` with phone-first styles.
  - System font stack, a 16px side gutter, and the page never scrolls sideways at 375px (FR-009).
  - Tab bar styles.
  - A compact `table.records`: small font, `white-space: nowrap` on numeric cells, the manager
    column allowed to wrap, right-aligned numbers, and zebra rows.
  - A `.notice` style for the ESPN-unavailable message.
- [X] T010 Create `src/belt/espn.py` following research.md §1–§6 and data-model.md
  (ManagerSeason, Season, cache rules). It reads `ESPN_LEAGUE_ID`, `ESPN_S2`, and `ESPN_SWID`
  from `os.environ`.
  - `current_season_year(today)`: `today.year` if `today.month >= 9`, else `today.year - 1`.
  - `fetch_season(year)`: one request via
    `League(league_id, year, espn_s2=..., swid=..., fetch_league=False).espn_request.league_get(params={"view": "mTeam"})`.
    It returns a `Season`:
    - Members are mapped by `id`.
    - Each team becomes a `ManagerSeason`, keyed by `team["primaryOwner"]` with the name
      `firstName lastName`. If the owner isn't in `members`, use `team["name"]` for both.
    - Record fields come from `team["record"]["overall"]`, and `final_rank` from
      `team.get("rankCalculatedFinal", 0)`.
    - `in_progress = status["latestScoringPeriod"] <= status["finalScoringPeriod"]`.
    - `previous_seasons = status["previousSeasons"]`.
  - `get_seasons()`: uses a module-level cache dict `{year: Season}`.
    - Fetch the current season if it's missing or more than 15 minutes old.
    - Then fetch any year from its `previous_seasons` that isn't cached yet. Completed seasons
      are never re-fetched.
    - It returns `(seasons_sorted_by_year, espn_error: bool)`. Any exception from a fetch is
      logged (never log the cookies), leaves the cache unchanged, and sets
      `espn_error = True`.

**Checkpoint**: `./scripts/dev-server.sh start`, then `curl 127.0.0.1:5002/healthz` returns `ok`.

---

## Phase 3: User Story 1 - See the all-time standings (Priority: P1) 🎯 MVP

**Goal**: The Records tab shows one row per manager with Yrs, W-L-T, Win%, PF, PA, and Titles,
grouped by ESPN member and ranked by win %, then points for.

**Independent Test**: Run quickstart.md "Local" steps 1–6. The table matches the baseline
there.

- [X] T011 [US1] Create `src/belt/records.py` with the pure function
  `all_time_records(seasons) -> list[AllTimeRecord]`, per data-model.md.
  - Group `ManagerSeason`s by `member_id`. Sum W/L/T and PF/PA, and count seasons.
  - `titles` counts seasons where `final_rank == 1`.
  - `win_pct = (wins + ties/2) / games`, or 0 when there are no games.
  - `name` comes from the manager's most recent season.
  - Sort by `(win_pct, points_for)` descending.
- [X] T012 [P] [US1] Create `tests/test_records.py` covering `all_time_records`. Build `Season`
  and `ManagerSeason` objects by hand; no ESPN calls.
  - Two seasons with different team names for the same `member_id` combine into one row.
  - The name comes from the latest season.
  - A tie counts as half a win.
  - Equal win % is broken by higher points for.
  - Titles count only seasons with `final_rank == 1`; a 0 rank in progress is not a title.
  - A manager who played fewer seasons shows the right `seasons` count.
- [X] T013 [US1] Add a `records` Blueprint to `src/belt/records.py` with route `GET /records`
  (endpoint `records.index`).
  - It calls `espn.get_seasons()` and `all_time_records(...)`.
  - It renders `records.html` with: the rows; the current season's year and `in_progress`; the
    current season's `fetched_at` for "Updated <time>"; and `espn_error`.
  - It always returns 200 (contracts/web-routes.md).
- [X] T014 [US1] Create `src/belt/templates/records.html`, extending `layout.html`, per
  contracts/web-routes.md.
  - Columns: Manager, Yrs, W-L-T, Win% (`.619` format), PF and PA as whole numbers, Titles.
  - Footnotes:
    - "Regular season only."
    - "<year> season in progress." (when it is)
    - "Updated <time>" (Mountain time, the LM's zone)
  - If `espn_error` is set and there are rows, show the notice "Couldn't reach ESPN. Showing
    records as of <time>." If there are no rows, show only "Couldn't reach ESPN. Try again
    later."
- [X] T015 [US1] Run `./scripts/check.sh` (tests pass), then walk through quickstart.md
  "Local" steps 1–6 against the dev server. Use the chrome-devtools MCP tools at a 375px
  viewport for the width check, and close the page afterwards. Fix anything that doesn't
  match.

**Checkpoint**: The Records tab works locally and matches the baseline.

---

## Phase 4: Deploy & Polish

**Purpose**: Ship it to `https://fantasy.taylorbasso.dev` and tidy up.

- [X] T016 [P] Create `deploy/deploy.py` by copying BB's `deploy/deploy.py`.
  - `APP_NAME = "for-the-belt"`, `URL = "https://fantasy.taylorbasso.dev"`.
  - Add PEP 723 inline metadata (`# /// script` with `dependencies = ["boto3[crt]>=1.34"]`)
    so it runs with `uv run deploy/deploy.py`.
- [X] T017 [P] Create the Terraform unit `~/code/basso-infra/basso-root/us-west-2/for-the-belt/`
  (`main.tf`, `variables.tf`, `outputs.tf`, `terragrunt.hcl`). Copy
  `~/code/basso-infra/basso-root/us-west-2/biweekly-budget/`, with `local.name = "for-the-belt"`,
  and change the following:
  - `domain` defaults to `fantasy.taylorbasso.dev`.
  - Add `variable "espn_league_id"` (string, no default; set with `TF_VAR_espn_league_id`).
  - Listener rule priority is 200.
  - Remove all DB pieces: `data.aws_rds_cluster.shared`, `data.aws_security_group.db`, the
    `db_from_task` rule, the `PG*` env vars, and the `db_password` locals and secret. Also
    remove the `secret_key` param and the `BUDGET_*` env vars.
  - Container environment: `ESPN_LEAGUE_ID = var.espn_league_id`.
  - Secrets: `ESPN_S2` from SSM `/for-the-belt/espn-s2` and `ESPN_SWID` from
    `/for-the-belt/espn-swid`. Update the execution role policy to allow only those two ARNs.
  - Remove the `db_endpoint` output.
  - Then run an offline `terraform init -backend=false && terraform validate && terraform fmt`
    in a scratch copy.
- [X] T018 Hand off to the LM (do not run these yourself; they create real AWS resources):
  - Create the two SSM SecureString parameters (quickstart.md "Deployed" step 1).
  - Run `eval "$(aws configure export-credentials --format env)"`, then
    `TF_VAR_espn_league_id=<id> terragrunt apply` in the new unit.
- [X] T019 After the LM confirms the apply, run `uv run deploy/deploy.py`
  (needs podman). Then run the quickstart.md "Deployed"
  checks 1–3: healthz, the records table from AWS, and that budget still loads.
- [X] T020 [P] Delete `scripts/lifetime_records.py`. Update `CLAUDE.md`:
  - Add a short "Commands" section: `scripts/dev-server.sh`, `scripts/check.sh`, and
    `uv run deploy/deploy.py`.
  - Note that the Records tab keeps no database (an in-memory cache), and that Postgres
    arrives with the bet tracker.
- [X] T021 [P] Replace `README.md` with a short description: what the app is, the live URL, how
  to run it locally (see quickstart.md), and how to deploy.

---

## Dependencies & Execution Order

- **Setup (T001–T005)**: T001 first (packaging); T002–T005 in parallel after it.
- **Foundational (T006–T010)**: after T001. T006 imports `belt.records`, so the app starts only
  once T013 exists. Until then, create a stub blueprint in `records.py` or register it in T013.
  T007–T009 in parallel. T010 is independent of T006–T009.
- **US1 (T011–T015)**: T011 needs T010's dataclasses. T012 runs in parallel with T013 and T014
  once T011 exists. T015 comes last.
- **Deploy & Polish (T016–T021)**: T016 and T017 can start any time. T018 needs T017 and the LM.
  T019 needs T015, T016, and T018. T020 and T021 can run any time after T015.

## Parallel Example: User Story 1

```text
After T011:  T012 (tests/test_records.py)  ‖  T014 (templates/records.html)
Then:        T013 (blueprint in records.py) → T015 (verify)
```

## Implementation Strategy

1. **MVP (local)**: Phases 1–3. The Records tab works on the dev server and matches the baseline.
2. **Ship**: Phase 4. Deploy to `fantasy.taylorbasso.dev` and share the link in the group chat.
3. **Next feature**: the weekly loser parlay tracker gets its own `/speckit-specify`. It adds
   Postgres, login, and a second tab without touching `records.py`.

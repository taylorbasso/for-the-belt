# for-the-belt

A companion app for an 8-person ESPN fantasy football league, run by the league manager (LM).
It tracks the things the league does outside the official ESPN app.

Project principles are in `.specify/memory/constitution.md`. This file and the constitution
must stay consistent.

## This is a hobby app. KISS.

This is a "for fun" app for eight friends, not a production system. Keep it simple, always.

- Build the simplest thing that works. When in doubt, leave it out.
- Don't handle rare edge cases (ties, duplicate picks, late submissions). The group sorts those out
  in the group chat. Add handling only after a case has actually caused a problem.
- Don't add input validation for league rules. The league polices itself.
- No speculative features, abstraction layers, or config for things that don't vary.
- Prefer fewer files, fewer dependencies, and fewer moving parts. Every new dependency or piece
  of infrastructure needs a clear reason.
- Tests are welcome for logic that's easy to get wrong (like finding the week's lowest scorer).
  Don't chase coverage.
- If a request seems to need something heavyweight, suggest the simpler option first.

## Stack and hosting

Mirror the LM's other app, `~/code/biweekly-budget`. Copy its patterns instead of inventing new
ones:

- Python 3.11, Flask, server-rendered Jinja templates, plain CSS, no front-end build step.
  Packaged with `pyproject.toml` (setuptools, `src/` layout), served by gunicorn on port 8000.
- PostgreSQL via `psycopg` 3 with plain SQL and no ORM. Connection comes from the standard `PG*`
  environment variables; `schema.sql` is applied at startup with idempotent statements.
- Auth (once needed): Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Werkzeug password hashing.
- `scripts/dev-server.sh {start|stop|restart|status}` for the local server, and `scripts/check.sh`
  for tests.
- Docker image built from `python:3.11-slim` for ARM64, running as a non-root user, with a
  `/healthz` route.
- Deploy with `deploy/deploy.py`: build with podman, push `:latest` to ECR, then force a new ECS
  deployment. The deploy script never touches the task definition.
- AWS infrastructure lives in the Terraform repo `~/code/basso-infra`, not here. That means one
  unit per app under `basso-root/us-west-2/`: ECR, ECS on Fargate Spot, ALB, ACM, Route 53, and
  secrets injected from SSM. The app gets its own database in the shared Aurora cluster via
  `tools/create_app_db.py`.
- Differences from the budget app:
  - **Shared ALB**: no new load balancer. Add a host-based listener rule for
    `fantasy.taylorbasso.dev` to the budget app's ALB, plus its certificate on the same HTTPS
    listener.
  - **Public**: members open it from iMessage links on their phones, from anywhere, so this
    host is open to the internet. The budget host stays limited to the LM's IP through its own
    listener rule.
  - **Own ECS cluster and service** named `for-the-belt`, like the budget app has. Clusters are
    free.
- Pages must work well at phone width.
- Auth: each member logs in with email and a salted, hashed password. The LM links each user's
  email to their ESPN member by hand.

## ESPN data

- ESPN has no official fantasy API. The app uses the undocumented endpoints through the
  [`espn-api`](https://github.com/cwendt94/espn-api) Python library. They can change without
  notice.
- Treat ESPN as read-only. Never try to write to ESPN.
- The league is viewable to the public, so the app sends no ESPN login. Don't add ESPN
  cookies (`espn_s2`) back: they'd be a full login to the LM's ESPN account.
- ESPN keeps seasons before 2026 private (past seasons' settings are locked), so 2022–2025
  come from `src/belt/data/past_seasons.json`, saved once while the LM's cookies still worked.
  Those seasons never change; don't regenerate the file.
- League history in ESPN goes back to 2022 under the current league ID.
- For grading parlay legs (real NFL games, not fantasy), ESPN's public NFL endpoints need no
  login. `scripts/nfl_week.py` wraps them; use them directly for other bet types:
  - `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=<season>&seasontype=2&week=<n>`:
    the week's games (`events[].id`), scores and `winner` flags. With no params it's the
    current week.
  - `https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=<id>`: one game.
    `boxscore.players[].statistics[]` has per-player stats by category (`rushing`,
    `receiving`, `passing`, `kickReturns`, `puntReturns`, `interceptions`, `defensive`), with
    `keys` naming each value in `athletes[].stats` (e.g. `rushingTouchdowns`,
    `receivingYards`). `scoringPlays[].text` reads like "Josh Allen 1 Yd Rush".
  - An anytime TD is any rushing, receiving, return or defensive TD. Passing TDs don't count.
  - `summary` also has `pickcenter[0]` (DraftKings): `homeTeamOdds.moneyLine`,
    `awayTeamOdds.moneyLine`, `spread` and `overUnder`, kept after the game.
  - These are a dev tool for Claude sessions. The app itself doesn't call them.

## Commands

```bash
./scripts/dev-server.sh {start|stop|restart|status}   # local server on 127.0.0.1:5002, loads .env
./scripts/check.sh                                     # pytest
uv run deploy/deploy.py                                # build, push, roll out (needs AWS creds + podman)
```

- First-time setup: `uv venv --python 3.11 .venv && uv pip install --python .venv -e '.[dev]'`.
- Restart the dev server after Python changes; templates reload on their own.
- AWS uses `aws login`. boto3 (so `deploy.py`) reads it directly, but the pinned Terraform AWS
  provider can't: run `eval "$(aws configure export-credentials --format env)"` before
  `terragrunt` in the same shell.
- Port 5001 belongs to the biweekly-budget dev server; don't stop it.

## Where things are

- `src/belt/espn.py`: ESPN reads, the in-memory season cache, `select_seasons()` for the
  season dropdown (markup in `templates/_season_picker.html`), and per-week lineups
  (`get_lineups()`, about 1 request per week, fetched 8 at a time), shared by all tabs.
- `src/belt/records.py`: the Records tab (aggregation + blueprint). The app has no database
  yet; Postgres arrives with an admin login, if one gets built.
- `src/belt/transactions.py`: the Transactions tab (pickups, drops, trades, lineup and IR
  moves from ESPN's per-team season totals).
- `src/belt/bench.py`: the Bench tab (best lineup in hindsight, lineup losses, worst week).
- `src/belt/parlays.py`: the Parlays tab (weekly loser parlay: leg records, parlay kills). Reads
  only `src/belt/data/parlays.json`, never ESPN.
- `specs/NNN-*/`: each feature's spec, plan, and tasks.
- Infrastructure: `~/code/basso-infra/basso-root/us-west-2/for-the-belt/`.

## Recording a parlay

Each week the lowest scorer (LSP) puts $10 on a parlay in a category they pick, and all eight
members, the LSP included, add one leg. The LM records it by asking Claude in a session.

- Add or edit the week in `src/belt/data/parlays.json` (shape in
  `specs/004-parlay-tracker/data-model.md`). Don't touch other weeks.
- `week` is the NFL week of the games bet on: the week after the LSP's loss.
- Use member names exactly as the other tabs show them: Taylor Basso, Jasper Bowser,
  Tate hathaway, Anthony Naranjo, Colton Dyches, Derek Parry, Dustin Vicchrilli,
  Cody Buckingham. A misspelled name splits that member's stats.
- `pick` is the leg as written on the slip. `odds` is American odds as an integer (`-150`,
  `240`), or null if unknown.
- `result` is `"W"`, `"L"`, or null until graded. `payout` is the dollars paid, only if it hit.
- `lsp` is the lowest scorer of the previous fantasy week (from ESPN's `pointsByScoringPeriod`).
- To grade, run `python3 scripts/nfl_week.py <season> <week>`: final scores with DraftKings'
  closing moneylines (use those as `odds` for ML legs) and every anytime-TD scorer, from
  ESPN's public NFL endpoints. Before marking a TD leg L, check the player shows up in that
  game's box score, so a name mismatch isn't graded as a loss. Spreads: grade from the final
  score and put the spread in `pick`, not `odds`. Other bet types get graded by hand.
- ESPN has no prices for anytime-TD props (the propBets entries are empty), so TD-leg odds only
  come from the bet slip. Don't go looking again.
- Then run `./scripts/check.sh`, commit, and deploy with `uv run deploy/deploy.py` (ask first).

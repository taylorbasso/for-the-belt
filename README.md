# For the Belt

A companion app for our ESPN fantasy football league: the stuff we track outside the official
ESPN app. Live at https://fantasy.taylorbasso.dev.

**Tabs**
- **Records**: all-time regular-season record, win %, points, and titles for every manager
  since 2022.

## Run locally

Needs Python 3.11 (via `uv`) and a `.env` with the league ID (see `.env.example`).

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv -e '.[dev]'
./scripts/check.sh
./scripts/dev-server.sh start      # http://127.0.0.1:5002
```

## Deploy

Infrastructure is in the `basso-infra` repo (`basso-root/us-west-2/for-the-belt`). To ship a
new version:

```bash
uv run deploy/deploy.py
```

How it's built and why is in `specs/` and `CLAUDE.md`.

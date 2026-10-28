# Quickstart: Bench Tab

Prerequisites, setup and deploy are the same as
[001 quickstart](../001-historical-records/quickstart.md).

## Validate locally

```bash
./scripts/check.sh
./scripts/dev-server.sh restart
open http://127.0.0.1:5002/bench
```

Expected:

1. The tab bar shows Records, Transactions and **Bench**. The page opens on 2026, with "season
   in progress".
2. Every "Points left / week" is at least 0, and rows are sorted worst first.
3. **All time**: the callout reads "Worst lineup ever: Anthony Naranjo, week 5 of 2024: started
   Brock Purdy (13.1) over Joe Burrow (37.8), leaving 62.2 points on the bench" (baseline
   2026-10-27).
4. **2022** has 6 rows. **All time** has 9, with no duplicates.
5. The first **All time** load after a restart takes a few seconds (about 6s). Reloading is
   instant.
6. At a 375px-wide viewport, no tab scrolls sideways.

## Validate after deploy

`uv run deploy/deploy.py`, then repeat steps 1, 3 and 4 on https://fantasy.taylorbasso.dev/bench.

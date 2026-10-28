# Quickstart: Transactions Tab

Prerequisites, setup and deploy are the same as
[001 quickstart](../001-historical-records/quickstart.md).

## Validate locally

```bash
./scripts/check.sh                       # all tests pass
./scripts/dev-server.sh restart          # Python changed
open http://127.0.0.1:5002/transactions
```

Expected:

1. The tab bar shows **Records** and **Transactions**, and Transactions is highlighted.
2. With no `?season`, the dropdown shows 2026 and the footnote says the season is in progress.
3. **2025** matches these ESPN counter values (baseline taken 2026-10-27):

   | Manager | Pickups | Drops | Trades | Lineup | IR |
   |---------|---------|-------|--------|--------|----|
   | Cody | 60 | 63 | 2 | 104 | 3 |
   | Dustin | 51 | 49 | 1 | 72 | 7 |
   | Derek | 50 | 53 | 4 | 138 | 3 |
   | Jasper | 45 | 46 | 1 | 85 | 0 |
   | Colton | 41 | 41 | 3 | 113 | 5 |
   | Taylor | 40 | 40 | 0 | 118 | 2 |
   | Anthony | 29 | 28 | 5 | 197 | 2 |
   | Tate | 24 | 25 | 2 | 97 | 4 |

4. **2022** has 6 rows. **All time** has 9 rows, and each manager appears once.
5. Records still works, and its dropdown behaves as before.
6. At a 375px-wide viewport, neither tab scrolls sideways.

## Validate after deploy

`uv run deploy/deploy.py`, then repeat steps 1–4 against https://fantasy.taylorbasso.dev/transactions.

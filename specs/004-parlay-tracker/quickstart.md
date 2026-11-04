# Quickstart: Parlay Tracker

Prerequisites, setup and deploy are the same as
[001 quickstart](../001-historical-records/quickstart.md).

## Record a week (the weekly routine)

1. In a Claude session in this repo, paste the bet slip or group chat: the LSP, the category,
   each member's leg and its odds.
2. Claude adds the parlay to `src/belt/data/parlays.json` (see [data-model.md](data-model.md)),
   with results null.
3. After the games, tell Claude which legs won and, if it hit, the payout. Claude fills in
   `result` and `payout`.
4. Commit, then `uv run deploy/deploy.py`.

## Validate locally

```bash
./scripts/check.sh
./scripts/dev-server.sh restart
open http://127.0.0.1:5002/parlays
```

Expected:

1. The tab bar shows Records, Transactions, Bench and **Parlays**.
2. With an empty file, the page shows "No parlays recorded yet."
3. With a sample week in the file (one L, seven W, all graded): the summary says 0 of 1 hit, the
   member with the L has Killed = 1 and is ranked first, and the week shows as Busted with their
   leg marked "killed it".
4. A week with some results null shows as Pending (or Busted if a leg has lost), and the null
   legs say "pending" and don't count in the table.
5. At a 375px-wide viewport, nothing scrolls sideways.

Put the file back to the real data after testing.

## Validate after deploy

`uv run deploy/deploy.py`, then open https://fantasy.taylorbasso.dev/parlays and repeat step 1,
and step 2 or 3 depending on what's recorded.

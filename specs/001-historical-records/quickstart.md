# Quickstart: Historical Records

How to prove the feature works, locally and once deployed. Routes and formats are in
[contracts/web-routes.md](contracts/web-routes.md).

## Local

Prerequisites: Python 3.11 and a `.env` with `ESPN_LEAGUE_ID`, `ESPN_S2` and `ESPN_SWID`
(see `.env.example`).

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv -e '.[dev]'
./scripts/check.sh                 # pytest
./scripts/dev-server.sh start      # http://127.0.0.1:5002
```

1. Open `http://127.0.0.1:5002/` and confirm it lands on the records tab.
2. Expect 9 managers: the 8 current members plus anyone who has left. Nobody should appear
   twice, despite team renames.
3. Confirm the totals against the baseline below, which `scripts/lifetime_records.py` captured
   at 2026 week 8. Each manager's row should match exactly, apart from current-season games
   played since then.

   | Manager | Yrs | W-L-T | Titles |
   |---------|-----|-------|--------|
   | Anthony Naranjo | 5 | 39-24-0 | 1 |
   | Taylor Basso | 5 | 39-24-0 | 1 |
   | Colton Dyches | 5 | 34-29-0 | 1 |
   | Cody Buckingham | 4 | 26-23-0 | 1 |
   | Dustin Vicchrilli | 4 | 24-25-0 | 0 |
   | Alex Langford | 2 | 12-16-0 | 0 |
   | Tate hathaway | 5 | 27-36-0 | 0 |
   | Jasper Bowser | 3 | 15-20-0 | 0 |
   | Derek Parry | 5 | 22-41-0 | 0 |

   Anthony ranks above Taylor because of the tiebreak on points for (FR-007).
4. Check that the footnote says the 2026 season is in progress.
5. In DevTools device mode at 375px wide, confirm the page doesn't scroll sideways.
6. **ESPN down**: load the page once, then set `ESPN_S2=bad` in `.env` and restart the dev
   server. Reload: expect "Couldn't reach ESPN. Try again later." (a fresh process has no
   cache). Then restore `.env`.

## Deployed (`https://fantasy.taylorbasso.dev`)

One-time setup:
1. Create the cookie parameters by hand, so they stay out of Terraform state:
   ```bash
   aws ssm put-parameter --name /for-the-belt/espn-s2 --type SecureString --value '<espn_s2>'
   aws ssm put-parameter --name /for-the-belt/espn-swid --type SecureString --value '<SWID>'
   ```
2. Apply the infra unit:
   `cd ~/code/basso-infra/basso-root/us-west-2/for-the-belt && terragrunt apply`

Every deploy:
- `python deploy/deploy.py` builds the image, pushes it, and rolls the service.

Checks after deploying:
1. `curl https://fantasy.taylorbasso.dev/healthz` → `ok`
2. On a phone, open `https://fantasy.taylorbasso.dev/` from an iMessage link. The table
   should match the local run. That also confirms ESPN accepts requests from AWS.
3. Confirm `https://budget.taylorbasso.dev/` still works (shared ALB).

**When ESPN cookies expire**: put fresh values in the SSM parameters (with `--overwrite`) and
re-run `python deploy/deploy.py`. ECS only reads secrets when a task starts.

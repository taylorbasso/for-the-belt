# Research: Historical Records

All findings were checked against the real league on 2026-10-27.

## 1. Where the data comes from: ESPN `mTeam` view, one request per season

- **Decision**: For each season, make one request through `espn-api`'s low-level client:
  `League(..., fetch_league=False).espn_request.league_get(params={"view": "mTeam"})`.
- **Rationale**: That single response has everything the tab needs:
  - `teams[].primaryOwner` and `teams[].record.overall` (wins, losses, ties, pointsFor,
    pointsAgainst)
  - `teams[].rankCalculatedFinal`
  - `members[]` (id, firstName, lastName)
  - `status.previousSeasons`, `status.latestScoringPeriod`, `status.finalScoringPeriod`

  Each request took 0.13–0.17s, so all five seasons (2022–2026) load in under a second.
- **Alternatives considered**: Calling `League(...)` with a full fetch, as
  `scripts/lifetime_records.py` does, also pulls rosters, matchups, the player list and the draft.
  That's far slower and needs nothing extra for this tab. Calling ESPN's raw HTTP endpoint without
  the library would mean re-implementing cookie and endpoint handling the library already does.

### 1a. Shotguns (added 2026-10-27)

- **Decision**: Add `mMatchupScore` to the same request (`view=["mTeam", "mMatchupScore"]`). Count
  the lowest score per NFL week from `pointsByScoringPeriod`, for weeks before
  `latestScoringPeriod`.
- **Rationale**: Still one request per season (about 0.17s). All 8 teams play every playoff week
  (winners and consolation brackets), so every week has a full set of scores. A cross-check on
  2026-10-27 found 79 shotguns, exactly one per completed week (4 × 18 + 7).

## 2. Storage: in-memory cache, no Postgres for this feature

- **Decision**: Keep fetched seasons in a module-level dict inside the app process.
  - Completed seasons are fetched once per process and never again; their results can't change.
  - The current season is re-fetched when its copy is more than 15 minutes old.
  - If ESPN fails, serve whatever is cached and show its "as of" time.
- **Rationale**: Under a second for a full refresh makes a database unnecessary. That's no
  schema, no DB credentials and no Aurora resume delay for this tab (KISS, Principle I). FR-010
  ("show the last loaded records") is met for as long as the process lives. Postgres arrives
  with the bet tracker, which actually needs to store user input.
- **Alternatives considered**:
  - **Store in Postgres**: survives restarts, but it adds the whole DB setup for one rare case,
    a Spot restart while ESPN happens to be down.
  - **Fetch on every page load**: simpler still, but rude to ESPN, and there'd be nothing to show
    when ESPN is down.
- **Accepted gap**: if the task restarts while ESPN is down, there's nothing cached yet, so the
  page shows "Couldn't reach ESPN. Try again later."

## 3. Which seasons exist: current season by date, past seasons from ESPN

- **Decision**: The current season is this calendar year from September onward, and last year
  from January through August. Past seasons come from that season's `status.previousSeasons`.
- **Rationale**: Each NFL season runs September to early January. Between seasons, the
  previous season is the latest one with games. There's no config to bump each year and no
  extra request.
- **Alternatives considered**:
  - An `ESPN_YEAR` setting: a yearly manual chore.
  - ESPN's game-level `currentSeasonId`: it rolls over before the league renews, so the league
    request would 404 for months.

## 4. Season in progress: compare scoring periods

- **Decision**: A season is in progress when `status.latestScoringPeriod <=
  status.finalScoringPeriod`.
- **Rationale**: `status.isActive` is `true` even for the completed 2025 season. The scoring
  periods tell the seasons apart: 2026 is 8 ≤ 18, so in progress; 2025 is 19 > 18, so complete.

## 5. Manager identity and names

- **Decision**: Group seasons by `team.primaryOwner`, the ESPN member GUID. The display name is
  `firstName lastName` from that member's most recent season. If a team's owner isn't in
  `members`, use the team name for that season.
- **Rationale**: Every team in every season has exactly one owner and a `primaryOwner`. Team
  names change from year to year; member ids don't.

## 6. Titles and the regular season

- **Decision**: A title is a season with `rankCalculatedFinal == 1`. W-L-T and points come from
  `record.overall`.
- **Rationale**: Completed seasons have ranks 1..N; the current season has all zeros, so it can't
  award a title early. These figures match the earlier script's output (wins and losses both
  totalled 238). 2022 had 6 teams; later seasons have 8. That fully explains the 38
  team-seasons, so nothing is missing.

## 7. Web stack: mirror biweekly-budget, minus what this feature doesn't use

- **Decision**: Flask with Jinja templates and plain CSS, served by gunicorn and packaged with
  `pyproject.toml` (`src/` layout), all copied from `~/code/biweekly-budget`. There's no
  database, sessions, CSRF, Flask-Login or `SECRET_KEY` yet. The tab is public (FR-011) and has
  no forms. Local config comes from `.env`, which `scripts/dev-server.sh` loads, so no
  `python-dotenv` in the app.
- **Rationale**: Reuse the LM's known patterns, and add the auth and DB pieces with the bet
  tracker when they're needed.

## 8. Hosting: new `for-the-belt` unit in basso-infra on the shared ALB

- **Decision**: Copy the biweekly-budget unit's ECR, log group, execution role, task SG, target
  group, ECS cluster, task definition (ARM64, 256 CPU / 512 MB) and Fargate Spot service.
  The differences:
  - A host-based listener rule on the shared `basso-apps` HTTPS listener: priority 200,
    `fantasy.taylorbasso.dev`.
  - A Route 53 alias to the shared ALB. No certificate; the wildcard covers it.
  - Secrets `ESPN_S2` and `ESPN_SWID` from SSM SecureString parameters
    `/for-the-belt/espn-s2` and `/for-the-belt/espn-swid`, created by hand.
  - `ESPN_LEAGUE_ID` as a plain environment variable.
  - No database access rules.
- **Risk**: ESPN might block requests from AWS IP ranges. Nothing in the community libraries
  suggests it does. The post-deploy check in quickstart.md confirms it.

## 9. Cookie expiry

- **Decision**: No automation.
- **Rationale**: When the LM's `espn_s2` stops working (after logging out, or eventually
  expiring), ESPN returns 401 and the page falls back to cached data or the "Couldn't reach
  ESPN" message. The LM updates the SSM parameters and re-runs the deploy script.
  quickstart.md documents this.

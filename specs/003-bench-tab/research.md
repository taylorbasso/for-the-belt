# Research: Bench Tab

All findings were checked against the real league on 2026-10-27 with a throwaway prototype.

## 1. Data: one request per week with `mMatchup` + `mMatchupScore`

- **Decision**: For each completed week `w`, request `view="mMatchup", scoringPeriodId=w`. Each team in that week's matchups has
  `rosterForCurrentScoringPeriod.entries[]`, and each entry has:
  - `lineupSlotId`: where the manager put the player. 20 = bench, 21 = IR.
  - `playerPoolEntry.appliedStatTotal`: the player's points that week.
  - `playerPoolEntry.player.fullName` and `player.eligibleSlots`.
- **Rationale**: Checked on every team-week from 2022 to 2026 (596 of them), including two-week
  playoff matchups:
  - Starters' points (everything except slots 20 and 21) add up exactly to ESPN's
    `pointsByScoringPeriod[w]` for that team (SC-002).
  - The best lineup is never below the actual one.
- **Why only `mMatchup`** (found after the first deploy): with `mMatchupScore` added, each
  week's response was about 2 MB, and a cold All time load took 25.6s on the 0.25-vCPU task,
  close to gunicorn's 30s timeout. `mMatchup` alone is about 0.8 MB and has every field above
  (checked on 48 team-weeks of 2024, playoffs included).
- **Alternatives considered**: espn-api's `League.box_scores(week)` returns the same thing
  wrapped in objects. It needs a full `League` fetch first, which is slower, and it hides the
  slot ids the math needs.

## 2. Lineup slots per season: `settings.rosterSettings.lineupSlotCounts`

- **Decision**: Read slot counts per season from `mSettings`, added to the first week's
  request. Ignore slots 20 (bench) and 21 (IR), and slots with a count of 0.
- **Rationale**: The league changed: 2022–2024 had 1 FLEX, and 2025–2026 have 2. Slot ids are
  0 QB, 2 RB, 4 WR, 6 TE, 16 D/ST, 17 K, 23 FLEX (RB/WR/TE).

## 3. Best lineup: greedy, most restrictive slot first

- **Decision**: List every starting slot. Sort the slots by how many of the manager's players
  could fill each one, fewest first, so QB/K/D/ST come before FLEX. For each slot, take the
  highest-scoring remaining eligible player. IR players aren't candidates.
- **Rationale**: Every flexible slot here (FLEX) accepts a superset of the positions of the
  fixed slots it overlaps. That makes filling restrictive slots first optimal for single-position
  players. Players eligible for more than one position are rare, and the prototype found no
  week where the result fell below the actual lineup. It's about 10 lines and easy to test.
- **Alternatives considered**: An exact assignment solver, or brute force over combinations.
  Correct in every case, but far more code for a difference that hasn't shown up.

## 4. Costliest swap (FR-004a)

- **Decision**: In the worst week:
  - **Pair**: of every benched player (slot 20) in the best lineup and every starter not in it
    whose `lineupSlotId` is in that bench player's `eligibleSlots`, take the pair with the
    biggest point gap.
  - The first rule tried (top bench scorer, paired with the worst starter he could replace)
    showed Kirk Cousins (24.2) for Patrick Mahomes (23.8) in a week that lost 56.5 points.
  - If there's no such pair (for example, the loss came from an empty slot), show only the week
    and points.
- **Example**: 2024 week 5, the all-time worst at 62.2 points left on the bench: Joe Burrow
  (37.8) was benched for Brock Purdy (13.1).

## 5. Lineup losses

- **Decision**: Use the season schedule's matchups that have both teams and a `winner` of
  `HOME` or `AWAY`. The loser has a lineup loss when the sum of their best possible scores, over
  the weeks in that matchup's `pointsByScoringPeriod`, is greater than the winner's
  `totalPoints`. Ties are skipped.
- **Rationale**: Handles two-week playoff matchups (spec edge case) with the same code as
  regular weeks. The schedule comes back with every weekly request, so nothing extra is fetched.

## 6. Fetching and caching

- **Decision**: `espn.fetch_lineups(year)` fetches every completed week of one season in
  parallel with a `ThreadPoolExecutor(8)`, plus `mSettings` once.
  - Weeks run from 1 to `min(latestScoringPeriod − 1, finalScoringPeriod)`, using the cached
    Season's status.
  - Results go in `_lineup_cache[year]`.
  - `espn.get_lineups(years)` fetches only seasons that are missing, or the current season once
    it's more than 15 minutes old.
  - On failure, it returns what's cached plus an error flag, like `get_seasons()`.
- **Rationale**:
  - The default view (current season) costs about 8 parallel requests.
  - All time cold took about 6s in the prototype, once per process. That's well within
    gunicorn's 30s timeout.
  - Completed seasons never change.
- **Alternatives considered**:
  - Sequential fetches: about 25s cold, too close to the timeout.
  - A startup warm-up thread: more moving parts for a one-time 6s wait.
  - Postgres: not here until the bet tracker.

## 7. Player identity across weeks

- **Decision**: The tab only shows names in the worst-week line, so store `fullName` per entry.
  No player ids.

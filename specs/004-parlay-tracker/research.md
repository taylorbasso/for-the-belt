# Research: Parlay Tracker

## 1. Storage: a JSON file in the repo, not Postgres

- **Decision**: Keep every parlay in `src/belt/data/parlays.json`. The LM records and grades
  weeks by asking Claude in a session, then commits and runs `uv run deploy/deploy.py`.
- **Rationale**: The LM is the only writer, and Claude is doing the writing. The data is tiny
  (about 150 legs a season). A file needs no schema, credentials, Aurora database, Aurora
  resume delay or auth. Git history is the audit trail for "that's not what I picked".
  `past_seasons.json` already works this way, and the `data/*` package-data rule already ships
  it.
- **Alternatives considered**:
  - **Postgres now**: the constitution expected it with this feature. But nothing writes from the
    web yet, so it would be setup with no payoff. It arrives with the admin login, if that's
    built, with a one-time import of this file.
  - **Fetch the file from S3 so updates skip a deploy**: one more moving part to save one
    command a week.
- **Accepted gap**: a recorded week shows on the site only after a deploy.

## 2. The LSP is recorded, not worked out from ESPN

- **Decision**: Each parlay stores the LSP's name.
- **Rationale**: It records what actually happened, it's one field, and it keeps the tab
  independent of ESPN (it works when ESPN is down and loads instantly).
- **Alternatives considered**: Reuse `shotguns_by_team` to find the week's lowest scorer. That
  couples the tab to ESPN for a name the LM types anyway.

## 3. Members are stored by display name

- **Decision**: Legs and the LSP use the member's name exactly as the other tabs show it (ESPN
  member first + last name): Taylor Basso, Jasper Bowser, Tate hathaway, Anthony Naranjo, Colton
  Dyches, Derek Parry, Dustin Vicchrilli, Cody Buckingham (2026 season).
- **Rationale**: Meets FR-009 without an ESPN lookup. Names are readable in the file and in git
  diffs.
- **Alternatives considered**: ESPN member IDs (`{GUID}` strings) mapped to names through ESPN.
  Unreadable when editing by hand, and it brings ESPN back in.
- **Accepted gap**: if a member changes their ESPN name, old weeks keep the old name. Fix the file
  by hand if it ever happens.

## 4. Implied chance from American odds

- **Decision**: Negative odds −X → X ÷ (X + 100). Positive odds +X → 100 ÷ (X + 100). A member's
  **expected hit rate** is the plain average over their graded legs that have odds.
- **Rationale**: That's the standard conversion. The average of implied chances is exactly the
  number of legs the odds expected to hit, divided by legs, so it compares directly with the
  actual hit rate.
- The vig makes it run a few points high, which is fine for a group-chat stat.
- Examples: −200 → 66.7%, +100 → 50%, +150 → 40%, −110 → 52.4%.

## 5. Parlay result and parlay killer

- **Decision**:
  - **Result**: busted if any leg is L, hit if every leg is W, pending otherwise.
  - **Parlay killer**: a member's leg is the only L in a parlay whose legs are all graded.
- **Rationale**: Straight from the spec. A single L with legs still pending isn't counted yet,
  because another leg could still lose.

## 6. Ranking and headline

- **Decision**: Members sorted by parlay-killer count (most first), then hit rate (lowest first),
  then name. Members with no graded legs go last. The headline counts hits among settled
  parlays, and total payouts.
- **Rationale**: The tab is for finding who keeps busting it (spec User Story 1). Members who
  haven't been graded can't be ranked.

## 7. No season picker yet

- **Decision**: Stats cover every recorded parlay; weeks show the season in their label once a
  second season exists.
- **Rationale**: FR-010. With one season of data, a dropdown would do nothing.

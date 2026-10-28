# Feature Specification: Historical Records

**Feature Branch**: `001-historical-records` (spec directory; no branch created)

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Historical records tab: all-time regular-season record, win %, points
for and against, and titles per manager across every ESPN season, grouped by ESPN member rather
than team name."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the all-time standings (Priority: P1)

A league member opens the Historical Records tab on their phone and sees one row per manager who
has ever played in the league. Each row shows seasons played, all-time regular-season record
(W-L-T), win %, total points for, total points against, and championships won. Managers are
ranked best to worst.

**Why this priority**: This is the whole feature. It settles "who's actually the best in this
league" arguments with real numbers.

**Independent Test**: Open the tab and compare each manager's totals against ESPN's final
standings for every season, added up by hand.

**Acceptance Scenarios**:

1. **Given** the league has seasons in ESPN, **When** a member opens the Historical Records tab,
   **Then** they see one row per manager with seasons played, W-L-T, win %, points for, points
   against, and titles.
2. **Given** a manager renamed their team between seasons, **When** the tab is shown, **Then**
   all of that manager's seasons are combined into a single row under the manager's name.
3. **Given** a manager who left the league after a few seasons, **When** the tab is shown,
   **Then** they still appear with totals from the seasons they played.
4. **Given** two managers have the same win %, **When** the tab is shown, **Then** the one with
   more total points for is ranked higher.
5. **Given** the current season is in progress, **When** the tab is shown, **Then** the totals
   include games already played this season, and the page says the current season is in
   progress.

### Edge Cases

- **ESPN is unavailable**: the tab shows the most recently loaded records with an "as of" date,
  plus a short message that ESPN couldn't be reached. It does not show an error page.
- **A team with no linked ESPN member** (e.g., an account that no longer exists): that team's
  season is shown under its team name instead of being dropped.
- **Seasons with a different number of teams**: totals reflect whatever ESPN reports for each
  season; nothing is normalized.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST have a Historical Records tab, reachable from the app's main
  navigation.
- **FR-002**: The tab MUST show, for each manager: seasons played, regular-season wins, losses,
  and ties (W-L-T), win %, total points for, total points against, and titles.
- **FR-003**: Records MUST be grouped by ESPN league member, not by team name.
- **FR-004**: Records MUST cover every season ESPN has for the league.
- **FR-005**: Win % MUST count a tie as half a win.
- **FR-006**: A title MUST count a season where the manager finished first overall.
- **FR-007**: Managers MUST be ranked by win %, with ties broken by total points for.
- **FR-008**: The tab MUST include the current season's games played so far and label the
  current season as in progress.
- **FR-009**: The tab MUST be readable at phone width without the page scrolling sideways.
- **FR-010**: If ESPN can't be reached, the tab MUST show the last loaded records with their
  "as of" date instead of an error.
- **FR-011**: The tab MUST be viewable by anyone with the link, without logging in.
- **FR-012**: The tab MUST show each manager's total shotguns: the number of completed NFL weeks,
  across every season and including playoff weeks, where they had the league's lowest score.
  Everyone tied for lowest gets one. (Added 2026-10-27.)

### Key Entities

- **Manager**: a person in the league, identified by their ESPN league member. Has a display name.
- **Manager season**: one manager's results for one season: wins, losses, ties, points for,
  points against, and final finish.
- **All-time record**: the totals for one manager across all their manager seasons, plus titles
  and seasons played.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every manager, the shown totals exactly match the sum of ESPN's final standings
  for each season they played.
- **SC-002**: Every manager who has ever played in the league appears exactly once.
- **SC-003**: A member can open the tab from an iMessage link and see the full table within
  3 seconds on a phone.
- **SC-004**: The tab still displays records when ESPN is unavailable.

## Assumptions

- "Every ESPN season" means every season ESPN has under the league's current league ID (2022
  onward). If the league existed earlier under a different ID, those seasons are out of scope.
- Only the regular season counts toward W-L-T and points. Shotguns (FR-012) are the exception:
  they count every completed week, playoffs included, back to 2022, even before the shotgun
  rule existed. Playoff records, head-to-head records,
  and per-season breakdowns are out of scope.
- Manager names come from their ESPN profile names.
- Records only need to be as fresh as the most recently completed week.
- The ranking is fixed; members can't re-sort the table.
- The tab is public because the stats aren't sensitive and it can ship before login exists. It
  can be moved behind login later if the league wants.

# Feature Specification: Transactions Tab

**Feature Branch**: `002-transactions-tab` (spec directory; no branch created)

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "ok I want a new tab to check, by year, the number of waiver pickups,
the number of player drops, what else could I do?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See who works the waiver wire (Priority: P1)

A league member opens the Transactions tab on their phone and sees one row per manager for the
chosen season: how many players they picked up, how many they dropped, and the other move counts
listed in FR-003. They can switch seasons, or pick "All time" for career totals, with the same
season dropdown the Records tab uses.

**Why this priority**: This is the whole feature. It settles "who lives on the waiver wire" and
"who set their lineup once in September and walked away" with real numbers.

**Independent Test**: Open the tab for a past season and compare each manager's counts with
their team's transaction totals in ESPN.

**Acceptance Scenarios**:

1. **Given** the league has seasons in ESPN, **When** a member opens the Transactions tab,
   **Then** they see the current season, one row per manager, with the counts in FR-003.
2. **Given** a member picks an earlier season, **When** the page reloads, **Then** the counts
   are for that season only.
3. **Given** a member picks "All time", **When** the page reloads, **Then** each manager's
   counts are summed across every season they played, combined under one row even if they
   renamed their team.
4. **Given** the current season is in progress, **When** the tab is shown, **Then** the counts
   include moves made so far and the page says the season is in progress.

### Edge Cases

- **ESPN is unavailable**: same as the Records tab. Show the last loaded counts with an "as of"
  time and a short message, never an error page.
- **A manager who left the league**: still appears in "All time" with the seasons they played,
  and in each of those seasons.
- **Pickups and drops don't match**: a manager can drop more players than they add (for
  example, after a 2-for-1 trade). The counts are shown as ESPN reports them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST have a Transactions tab, reachable from the app's main navigation
  next to Records.
- **FR-002**: The tab MUST have the same season dropdown as Records: every season, newest first,
  plus "All time", defaulting to the current season.
- **FR-003**: For each manager, the tab MUST show:
  - pickups: players added from waivers or free agency
  - drops: players released
  - trades: trades they were part of
  - lineup moves: players moved into the starting lineup
  - IR moves: players moved to injured reserve
- **FR-004**: Counts MUST cover the whole season, playoffs included.
- **FR-005**: Managers MUST be grouped by ESPN league member, not team name, as on Records.
- **FR-006**: Managers MUST be ranked by pickups, most first.
- **FR-007**: The tab MUST be readable at phone width without the page scrolling sideways.
- **FR-008**: If ESPN can't be reached, the tab MUST show the last loaded counts with their
  "as of" time instead of an error.
- **FR-009**: The tab MUST be viewable by anyone with the link, without logging in.

### Key Entities

- **Manager season moves**: one manager's move counts for one season: pickups, drops, trades,
  lineup moves, and IR moves.
- **All-time moves**: a manager's counts summed across every season they played.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every manager and season, the shown counts exactly match ESPN's transaction
  totals for that team.
- **SC-002**: Every manager who has played in a season appears exactly once for that season, and
  exactly once in "All time".
- **SC-003**: A member can open the tab from an iMessage link and see the table within
  3 seconds on a phone.

## Assumptions

- "Waiver pickups" means every player added, whether claimed off waivers or picked up as a free
  agent. ESPN counts them together. The league uses standard waivers with no FAAB budget, so
  there are no bid amounts to show.
- Players received in trades are not pickups.
- A trade counts once for each manager in it, so the league total of the trades column is twice
  the number of trades.
- Lineup moves count every time a player is put into the starting lineup, as ESPN tallies it.
  Benching a player isn't counted separately.
- Seasons are the same ones Records covers: 2022 onward under the current league ID.
- Per-move details (which player, which week) are out of scope; the tab shows counts only.
- Like Records, the tab is public and needs no login.

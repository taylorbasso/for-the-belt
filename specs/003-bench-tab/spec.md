# Feature Specification: Bench Tab

**Feature Branch**: `003-bench-tab` (spec directory; no branch created)

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Bench tab: per manager, by season and all time (same season
dropdown), how well they set their lineup. Lineup % (points started ÷ best possible lineup in
hindsight, respecting lineup slots), points left on bench per week, and lineup losses (losses
the best lineup would have won). Counts every week, playoffs included."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find out who can't set a lineup (Priority: P1)

A league member opens the Bench tab on their phone and sees, for each manager in the chosen
season (or all time), how close their starting lineups came to the best lineup they could have
set in hindsight. They also see how many points each manager left on the bench per week, and
how many games they lost only because of who they started. A deep bench by itself doesn't count
against anyone; only starting the wrong players does.

**Why this priority**: This is the whole feature. It answers "who's a bad manager" with a number
that doesn't punish managers just for having a good bench.

*Layout revised after first deploy; see FR-008a.*

**Independent Test**: Pick a few manager weeks, work out each best possible lineup from that
week's roster by hand, and compare with the app's numbers for those weeks. Then check that a
season's row adds up its weeks.

**Acceptance Scenarios**:

1. **Given** a week where every bench player scored less than every starter they could have
   replaced, **When** the tab is shown, **Then** that manager left 0 points on the bench that
   week.
2. **Given** a week where a bench WR scored 25 and the starting WR scored 6, with no other
   better options, **When** the tab is shown, **Then** that manager left 19 points on the bench
   that week.
3. **Given** a matchup a manager lost, where their best possible lineup would have outscored
   the opponent's actual score, **When** the tab is shown, **Then** it counts as one lineup
   loss.
4. **Given** a member picks a season or "All time" in the dropdown, **When** the page reloads,
   **Then** the numbers cover only those seasons, one row per manager.
5. **Given** the current season is in progress, **When** the tab is shown, **Then** it includes
   completed weeks only and says the season is in progress.
6. **Given** a manager's biggest blunder in the selected seasons was week 9 of 2024, where they
   left 29.3 points on the bench by starting a WR who scored 2.1 over a bench WR who scored 31.4,
   **When** the tab is shown, **Then** their worst week reads like "Wk 9 '24: −29.3, benched
   [bench WR] (31.4) for [starting WR] (2.1)".

### Edge Cases

- **Two-week playoff matchups**: each week's lineup is judged on its own. A lineup loss compares
  the best possible scores for both weeks combined with the opponent's actual combined score.
- **Empty lineup slots**: a slot left empty counts as 0 points started. The best lineup fills it
  from the bench if anyone eligible scored.
- **Injured reserve**: players in the IR slot can't be used in the best lineup.
- **Players who were ruled out late or didn't play**: they scored 0, so starting them only
  costs whatever a bench player in an eligible slot would have scored instead.
- **ESPN is unavailable**: same as the other tabs. Show what's loaded with an "as of" time, or a
  short message, never an error page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST have a Bench tab, reachable from the main navigation next to Records
  and Transactions.
- **FR-002**: The tab MUST have the same season dropdown as the other tabs: every season, newest
  first, plus "All time", defaulting to the current season.
- **FR-003**: For each week, a manager's **best possible score** MUST be the highest score they
  could have started from that week's roster, filling the league's lineup slots (1 QB, 2 RB,
  2 WR, 1 TE, 2 FLEX, 1 D/ST, 1 K), with each player only in a slot their position allows.
- **FR-004**: For each manager, the tab MUST show:
  - **Points left per week**: (total best possible − total started) ÷ weeks played.
  - **Games blown** (lineup losses): matchups they lost where their best possible score would
    have beaten the opponent's actual score.
  - **Worst week**: the single week, in the selected seasons, where they left the most points
    on the bench. Show the week, the season, the points left, and the swap that cost the most.
- **FR-004a**: The **swap that cost the most** MUST be the pair with the biggest point gap
  between a benched player who was in the best lineup and a starter who wasn't, whose slot that
  bench player could have filled. Each is shown with their name and points. (Revised during
  implementation: pairing the top bench scorer with the worst starter he could replace picked a
  0.4-point QB swap in a 56.5-point week.)
- **FR-005**: Every completed week counts, including all playoff and consolation weeks. The
  week in progress doesn't count.
- **FR-006**: Managers MUST be grouped by ESPN league member, not team name.
- **FR-007**: Managers MUST be ranked by points left per week, worst first.
- **FR-008**: The tab MUST open with a plain-language headline and one-sentence explanation
  (including that it's in hindsight), then call out the single worst week in the selected
  seasons as a sentence: who, which week, the costliest swap, and the points left.
- **FR-008a** (revised after first deploy, 2026-10-27): The LM found the first layout unclear:
  Lineup %, Bench/wk and L. losses columns with a dense worst-week line. Lineup % was dropped
  because it said the same thing as points left per week, less concretely. Column names are
  plain words.
- **FR-009**: The tab MUST be readable at phone width without sideways scrolling.
- **FR-010**: If ESPN can't be reached, the tab MUST show the last loaded numbers with their
  "as of" time instead of an error.
- **FR-011**: The tab MUST be viewable by anyone with the link, without logging in.

### Key Entities

- **Manager week**: one manager's week: points started, best possible points, the swap that
  cost the most (if any), and (when a matchup ends that week) whether it was a loss the best
  lineup would have won.
- **Bench record**: a manager's totals across the selected weeks: points started, best possible
  points, weeks played, lineup losses, and their worst week.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a hand-checked sample of manager weeks, the best possible score, points left
  on the bench, and the costliest swap match a manual calculation exactly.
- **SC-002**: Points started for each manager and week match the score ESPN shows for that week.
- **SC-003**: Every manager appears exactly once per season and once in "All time".
- **SC-004**: Once the league's history has been loaded after a restart, a member opening the
  tab from an iMessage link sees the table within 3 seconds on a phone.

## Assumptions

- "Best possible lineup" uses only players on the manager's roster that week (bench and
  starters, not IR). It doesn't consider free agents or trades.
- The league's lineup slots are taken from each season's ESPN settings, so a season with
  different slots is judged by its own rules. The slots listed in FR-003 are the current ones.
- Seasons are the same ones Records covers: 2022 onward.
- If two weeks tie for worst, either one is fine.
- If a manager never left points on the bench in the selected seasons, their worst week is
  shown as a dash.
- Like the other tabs, it's public and needs no login.

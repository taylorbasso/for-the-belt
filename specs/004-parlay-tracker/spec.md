# Feature Specification: Parlay Tracker

**Feature Branch**: `004-parlay-tracker` (spec directory; no branch created)

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "Weekly loser parlay tracker (Parlays tab). Each fantasy week, the
league's lowest scoring player (LSP) shotguns a beer and puts $10 on a parlay. The LSP picks a
category for the bet (free text), and every member, the LSP included, picks exactly one leg, so
8 legs. The parlay is on the following week's NFL games. Record per week: the LSP, the category,
each member's leg (free text), its American odds, its result (W or L), and the payout if the
parlay hit. The parlay hits only if every leg wins. The LM enters each week through a Claude
session; no entry form or logins yet. Show each week's parlay and per-member stats: leg W-L,
hit rate, and a 'parlay killer' count (weeks where their leg was the only loser)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find out who keeps busting the parlay (Priority: P1)

A league member opens the Parlays tab from an iMessage link on their phone. They see one row per
member: how many of their legs won and lost, their hit rate, how often the odds said their legs
should hit, and how many times theirs was the only leg that lost, killing a parlay that would
otherwise have hit. Members are ranked so the worst pickers are at the top.

**Why this priority**: This is why the LM wants to track it at all: the hunch that some members
can't pick a leg and keep busting the parlay.

**Independent Test**: With a few recorded weeks, count each member's wins, losses and sole
losing legs by hand and compare with the table.

**Acceptance Scenarios**:

1. **Given** a member's legs went W, L, W, W across four graded weeks, **When** the tab is
   shown, **Then** their record reads 3-1 and their hit rate 75%.
2. **Given** a week where seven legs won and one member's leg lost, **When** the tab is shown,
   **Then** that member's parlay-killer count goes up by one, and nobody else's does.
3. **Given** a week where two legs lost, **When** the tab is shown, **Then** neither of those
   members gets a parlay-killer count for that week, and both get a loss.
4. **Given** a member picked legs at −200 and +100, **When** the tab is shown, **Then** their
   expected hit rate is the average of the odds' implied chances (66.7% and 50%), so 58.3%.
5. **Given** a member who hasn't had any graded legs yet, **When** the tab is shown, **Then**
   they appear with a 0-0 record and dashes for the rates.

---

### User Story 2 - See each week's parlay (Priority: P2)

Below the table, a member sees every recorded week, newest first: who the LSP was, the category
they chose, and the eight legs with who picked each one, its odds and its result. Each week says
whether the parlay hit, busted or is still pending, and what it paid if it hit.

**Why this priority**: This is the receipt. It settles "what did you even pick that week"
arguments, and it's how the LM checks the week was recorded right.

**Independent Test**: Record one week by hand and check that the tab shows it exactly as
entered.

**Acceptance Scenarios**:

1. **Given** the week 9 LSP set a "NFL RB anytime TD only" parlay on week 10 games, **When**
   the tab is shown, **Then** that parlay is labeled as week 10, names the LSP and shows the
   category.
2. **Given** all eight legs won and the LM recorded a $412.50 payout, **When** the tab is shown,
   **Then** the week shows as a hit that paid $412.50.
3. **Given** one leg has lost and others haven't been graded yet, **When** the tab is shown,
   **Then** the week shows as busted, and the ungraded legs show as pending.
4. **Given** no leg has lost and some legs haven't been graded yet, **When** the tab is shown,
   **Then** the week shows as pending.

---

### User Story 3 - Record a week (Priority: P1)

Each week, the LM tells Claude the LSP, the category and each member's leg with its odds, for
example by pasting the bet slip or the group chat. After the games, the LM tells Claude which
legs won and, if the parlay hit, the payout. Claude updates the stored record, and the change
shows on the site after the LM deploys.

**Why this priority**: Without it, there's nothing to show. It's P1 alongside Story 1.

**Independent Test**: Record a new week and grade it in a Claude session, deploy, and confirm
the tab shows it.

**Acceptance Scenarios**:

1. **Given** the LM pastes a bet slip with eight legs and odds, **When** Claude records the
   week, **Then** each leg is stored against the right member, with its text as written on the
   slip and its odds.
2. **Given** a recorded week, **When** the LM gives the leg results, **Then** each leg is marked
   W or L, and the payout is stored if all eight won.

### Edge Cases

- **A week in progress**: ungraded legs show as pending. They don't count toward any record,
  hit rate, expected hit rate or parlay-killer count until graded.
- **Parlay-killer counts on unfinished weeks**: a sole-loser count needs every leg graded. A
  week with one loss and some legs still pending gives no parlay-killer count yet.
- **Backfilled weeks with missing details**: if the odds or payout for an old week can't be
  found, leave them blank. Blank odds are left out of the expected hit rate; the leg still
  counts toward the W-L record.
- **No weeks recorded yet**: the tab shows a short line saying no parlays have been recorded,
  not an empty table.
- **ESPN is unavailable**: this tab doesn't read anything from ESPN, so it still works.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST have a Parlays tab, reachable from the main navigation next to the
  other tabs.
- **FR-002**: For each recorded parlay, the app MUST keep: the season, the NFL week of the games
  bet on, the LSP who set it, the category (free text), the payout if it hit, and exactly one leg
  per member.
- **FR-003**: For each leg, the app MUST keep: the member who picked it, the leg as written
  (free text), its American odds, and its result: W, L, or not yet graded.
- **FR-004**: A parlay's result MUST be worked out from its legs: **busted** if any leg lost,
  **hit** if all legs won, and **pending** otherwise.
- **FR-005**: For each member, the tab MUST show:
  - **Record**: graded legs won and lost (e.g. 6-3).
  - **Hit rate**: legs won ÷ legs graded.
  - **Expected hit rate**: the average implied chance of their graded legs from the odds
    (a −200 leg is 66.7%, a +150 leg is 40%). Comparing it to the hit rate shows whether a member
    is unlucky or just picks long shots.
  - **Parlay killer**: weeks with every leg graded where their leg was the only one that lost.
- **FR-006**: Members MUST be ranked by parlay-killer count, most first, then by hit rate,
  lowest first.
- **FR-007**: The tab MUST list every recorded parlay, newest first, with its week, LSP,
  category, result, payout (if it hit) and each leg's picker, text, odds and result.
- **FR-008**: The tab MUST open with a plain-language headline and a one-sentence summary, such
  as how many parlays have hit out of how many were settled.
- **FR-009**: Members MUST be shown by the same names the other tabs use for ESPN league members,
  so the same person reads the same everywhere.
- **FR-010**: Stats MUST cover every recorded week. (A season picker can come once a second
  season has parlays.)
- **FR-011**: The tab MUST be readable at phone width without sideways scrolling.
- **FR-012**: The tab MUST be viewable by anyone with the link, without logging in.
- **FR-013**: The LM MUST be able to add a week, and later grade it, by asking Claude in a
  session. No in-app entry form is needed.

### Key Entities

- **Parlay**: one week's bet: season, NFL week of the games, LSP, category, payout if it hit,
  and its eight legs. Its result is worked out from the legs.
- **Leg**: one member's pick in a parlay: who picked it, the text as written, American odds, and
  W, L or not yet graded.
- **Member parlay record**: a member's totals across every recorded week: wins, losses, hit
  rate, expected hit rate and parlay-killer count. Worked out from the legs, not stored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a hand-checked set of weeks, every member's record, hit rate, expected hit rate
  and parlay-killer count match a manual calculation exactly.
- **SC-002**: Recording a new week from a pasted bet slip takes the LM under 5 minutes, including
  the deploy.
- **SC-003**: A member opening the tab from an iMessage link sees it within 3 seconds on a phone.
- **SC-004**: Every recorded leg appears on the tab exactly as it was entered.

## Assumptions

- The LM is the only person who records parlays. They do it in a Claude session, and the data
  lives with the app's code. A change shows on the site after a deploy. If an admin login and
  entry form are built later, the recorded weeks move over with them.
- The LSP is recorded as part of each parlay instead of being worked out from ESPN scores. That
  records what actually happened and keeps this tab working when ESPN is down.
- Every member picks exactly one leg every week, there's one LSP each week, and legs only win or
  lose. Ties for LSP, missing legs, pushes, voided legs and cash-outs don't happen; the league
  sorts out any that do in the group chat.
- The stake is always $10, so it isn't recorded per week.
- Each parlay is on the NFL week after the fantasy week the LSP lost. It's labeled by the NFL
  week of its games.
- Tracking starts in the 2026 season. Earlier weeks are backfilled where the LM can find them;
  missing weeks are fine.
- Parlay and leg details are fine to show publicly, like the other tabs.
- The app records outcomes only. Money moves through the league's betting app.

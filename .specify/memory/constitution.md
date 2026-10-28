<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.0.1 (PATCH)
  - III. One Small App: "existing ECS cluster" → "Fargate Spot, sharing the existing load
    balancer" (the app gets its own free ECS cluster; no new ALB)
Previous change: (unfilled template) → 1.0.0
Modified principles (initial adoption):
  - [PRINCIPLE_1_NAME] → I. KISS: It's a Hobby App (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. ESPN Is Read-Only and Unofficial
  - [PRINCIPLE_3_NAME] → III. One Small App
  - [PRINCIPLE_4_NAME] → IV. Phone-First, Logged-In Members
  - [PRINCIPLE_5_NAME] → V. Features Are Tabs
Added sections:
  - Secrets & Data (was [SECTION_2_NAME])
  - Development Workflow (was [SECTION_3_NAME])
Removed sections: none
Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check is filled per plan; no change)
  - ✅ .specify/templates/spec-template.md (no new mandatory sections; no change)
  - ✅ .specify/templates/tasks-template.md (tests already optional; matches Development Workflow)
  - ✅ .claude/skills/speckit-*/SKILL.md (generic constitution references; no change)
  - ✅ CLAUDE.md (added pointer to this constitution)
Follow-up TODOs: none
-->

# For the Belt Constitution

## Core Principles

### I. KISS: It's a Hobby App (NON-NEGOTIABLE)

For the Belt is a "for fun" app for eight friends, not a production system.

- Build the simplest thing that works. When in doubt, leave it out.
- Do not handle rare edge cases (ties, duplicate picks, late submissions) or validate league
  rules. The league sorts those out in the group chat.
- Add handling for a case only after it has actually caused a problem.
- No speculative features, abstraction layers, or configuration for things that don't vary.

Rationale: one person maintains this in their spare time. Simplicity is what keeps it fun.

### II. ESPN Is Read-Only and Unofficial

- ESPN data comes from the undocumented fantasy endpoints via the `espn-api` Python library.
- The app MUST NOT write to ESPN.
- ESPN can change or break without notice. When ESPN fails, the app MUST still load and show
  what it has stored, plus an error message. It MUST NOT crash.

Rationale: there is no official API and no support, so ESPN is a convenience, not a dependency
the app can't live without.

### III. One Small App

- One Python app in one container on Fargate Spot, deployed the same way as the LM's other apps
  and sharing their existing load balancer.
- Server-rendered HTML with no front-end build step and no SPA framework.
- Data the app owns lives in the LM's shared Postgres instance, in its own schema or database
  so it can't collide with other apps.
- New dependencies or infrastructure (queues, caches, extra services) need a clear, current
  reason written in the plan.

Rationale: fewer moving parts means less to break and less to remember.

### IV. Phone-First, Logged-In Members

- Members open the app from iMessage links, so every page MUST work at phone width.
- Each member logs in with email and password. Passwords MUST be stored salted and hashed with
  a standard library algorithm, never in plain text.
- Each account is tied to one ESPN league member. The LM sets that mapping by hand; there is no
  self-service signup.

Rationale: logins give each person exactly one submission per week, and phones are where the
league actually is.

### V. Features Are Tabs

- The app will grow. Each feature is its own tab or page (the first two are the weekly loser
  parlay tracker and historical records).
- A feature MUST work on its own; removing one tab MUST NOT break another.
- Share code between features only once two features actually need the same thing.

Rationale: lets new ideas get added, or dropped, without reworking the rest of the app.

## Secrets & Data

- ESPN cookies (`espn_s2`, `SWID`), database credentials, and other secrets live in environment
  variables (`.env` locally, task configuration on ECS). They MUST NOT be committed or logged.
- Store only what a feature needs: email, display name, ESPN member link, and feature data.
- No money handling. Payments and payouts stay in the league's betting app.

## Development Workflow

- Use the Spec Kit flow (`/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
  `/speckit-implement`) for new features. Small fixes can go straight to a commit.
- Tests are optional. Add them for logic that's easy to get wrong (like finding the week's
  lowest scorer). Don't chase coverage.
- Each plan's Constitution Check confirms the design follows Principles I–V. Anything that
  breaks one goes in Complexity Tracking with a reason, or the design gets simpler.

## Governance

This constitution guides every spec, plan, and task. `CLAUDE.md` holds day-to-day guidance and
MUST stay consistent with it.

- **Amendments**: update this file with `/speckit-constitution` and record the change in the
  Sync Impact Report at the top.
- **Versioning**: MAJOR for removing or redefining a principle, MINOR for adding a principle or
  section, PATCH for wording fixes.
- **Compliance**: checked in each plan's Constitution Check and by `/speckit-analyze`.

**Version**: 1.0.1 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-27

"""Read league data from ESPN's unofficial fantasy API (read-only), with an in-memory cache.

Completed seasons never change, so each is fetched once per process. The current season is
re-fetched when its copy is more than 15 minutes old. If ESPN fails, callers get whatever is
cached plus an error flag.
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from espn_api.football import League

log = logging.getLogger(__name__)

CURRENT_SEASON_MAX_AGE = timedelta(minutes=15)


@dataclass(frozen=True)
class ManagerSeason:
    year: int
    team_id: int
    member_id: str
    name: str
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    final_rank: int  # 0 while the season is in progress
    shotguns: int  # completed weeks with the league's lowest score, playoffs included
    pickups: int  # players added from waivers or free agency; the rest are ESPN's season totals
    drops: int
    trades: int  # counted once for each team in the trade
    lineup_moves: int  # players moved into the starting lineup
    ir_moves: int


@dataclass(frozen=True)
class Season:
    year: int
    managers: list[ManagerSeason]
    in_progress: bool
    previous_seasons: list[int]
    fetched_at: datetime
    last_completed_week: int = 0


@dataclass(frozen=True)
class Player:
    name: str
    slot: int  # ESPN lineup slot the manager put them in: 20 = bench, 21 = IR
    points: float
    eligible: frozenset[int]  # lineup slots their position allows


@dataclass(frozen=True)
class TeamWeek:
    week: int
    team_id: int
    players: list[Player]


@dataclass(frozen=True)
class Matchup:
    weeks: list[int]  # two weeks for playoff matchups
    winner_id: int
    loser_id: int
    winner_points: float


@dataclass(frozen=True)
class Lineups:
    """Every completed week's rosters for one season."""

    year: int
    slot_counts: dict[int, int]  # starting slots only
    team_weeks: list[TeamWeek]
    matchups: list[Matchup]
    fetched_at: datetime


BENCH, IR = 20, 21

_cache: dict[int, Season] = {}
_lineup_cache: dict[int, Lineups] = {}


def current_season_year(today: date) -> int:
    """NFL seasons run September to early January; between seasons, the last one is current."""
    return today.year if today.month >= 9 else today.year - 1


def shotguns_by_team(schedule: list[dict[str, Any]], latest_scoring_period: int) -> dict[int, int]:
    """Count, per team id, the completed NFL weeks where it had the lowest score.

    Uses per-week points, since playoff matchups span two weeks. Weeks before ESPN's
    latestScoringPeriod are complete. Everyone tied for lowest gets one.
    """
    weekly: dict[int, dict[int, float]] = {}
    for matchup in schedule:
        for side in ("home", "away"):
            team = matchup.get(side)
            if not team:
                continue
            for week, points in team.get("pointsByScoringPeriod", {}).items():
                if int(week) < latest_scoring_period:
                    weekly.setdefault(int(week), {})[team["teamId"]] = points

    counts: dict[int, int] = {}
    for scores in weekly.values():
        low = min(scores.values())
        for team_id, points in scores.items():
            if points == low:
                counts[team_id] = counts.get(team_id, 0) + 1
    return counts


def _league_get(year: int, params: dict[str, Any]) -> dict[str, Any]:
    league = League(
        league_id=int(os.environ["ESPN_LEAGUE_ID"]),
        year=year,
        espn_s2=os.environ["ESPN_S2"],
        swid=os.environ["ESPN_SWID"],
        fetch_league=False,
    )
    return league.espn_request.league_get(params=params)


def fetch_season(year: int) -> Season:
    data = _league_get(year, {"view": ["mTeam", "mMatchupScore"]})
    status = data["status"]
    members = {m["id"]: m for m in data.get("members", [])}
    shotguns = shotguns_by_team(data.get("schedule", []), status["latestScoringPeriod"])

    managers = []
    for team in data["teams"]:
        member = members.get(team.get("primaryOwner"))
        if member:
            member_id = member["id"]
            name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
        else:
            member_id = name = team.get("name", f"Team {team['id']}")
        record = team["record"]["overall"]
        moves = team.get("transactionCounter", {})
        managers.append(
            ManagerSeason(
                year=year,
                team_id=team["id"],
                member_id=member_id,
                name=name or member_id,
                wins=record["wins"],
                losses=record["losses"],
                ties=record["ties"],
                points_for=record["pointsFor"],
                points_against=record["pointsAgainst"],
                final_rank=team.get("rankCalculatedFinal") or 0,
                shotguns=shotguns.get(team["id"], 0),
                pickups=moves.get("acquisitions", 0),
                drops=moves.get("drops", 0),
                trades=moves.get("trades", 0),
                lineup_moves=moves.get("moveToActive", 0),
                ir_moves=moves.get("moveToIR", 0),
            )
        )

    return Season(
        year=year,
        managers=managers,
        in_progress=status["latestScoringPeriod"] <= status["finalScoringPeriod"],
        previous_seasons=list(status.get("previousSeasons", [])),
        fetched_at=datetime.now(timezone.utc),
        last_completed_week=min(status["latestScoringPeriod"] - 1, status["finalScoringPeriod"]),
    )


def fetch_lineups(season: Season) -> Lineups:
    """One request per completed week, 8 at a time (about 1s for a full season)."""
    weeks = list(range(1, season.last_completed_week + 1))

    def get_week(week: int) -> dict[str, Any]:
        views = ["mMatchup"] + (["mSettings"] if week == 1 else [])  # mMatchupScore adds ~1 MB
        return _league_get(season.year, {"view": views, "scoringPeriodId": week})

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(get_week, weeks))

    slot_counts: dict[int, int] = {}
    if responses:
        counts = responses[0]["settings"]["rosterSettings"]["lineupSlotCounts"]
        slot_counts = {int(s): n for s, n in counts.items() if n and int(s) not in (BENCH, IR)}

    team_weeks = []
    for week, data in zip(weeks, responses):
        for matchup in data.get("schedule", []):
            for side in ("home", "away"):
                team = matchup.get(side)
                if not team or "rosterForCurrentScoringPeriod" not in team:
                    continue
                if str(week) not in team.get("pointsByScoringPeriod", {}):
                    continue
                players = [
                    Player(
                        name=e["playerPoolEntry"]["player"]["fullName"],
                        slot=e["lineupSlotId"],
                        points=e["playerPoolEntry"]["appliedStatTotal"],
                        eligible=frozenset(e["playerPoolEntry"]["player"]["eligibleSlots"]),
                    )
                    for e in team["rosterForCurrentScoringPeriod"]["entries"]
                ]
                team_weeks.append(TeamWeek(week, team["teamId"], players))

    matchups = []
    for m in responses[-1].get("schedule", []) if responses else []:
        home, away = m.get("home"), m.get("away")
        if not home or not away or m.get("winner") not in ("HOME", "AWAY"):
            continue
        played = [int(w) for w in home.get("pointsByScoringPeriod", {})]
        if not played or max(played) > season.last_completed_week:
            continue
        winner, loser = (home, away) if m["winner"] == "HOME" else (away, home)
        matchups.append(Matchup(sorted(played), winner["teamId"], loser["teamId"], winner["totalPoints"]))

    return Lineups(season.year, slot_counts, team_weeks, matchups, datetime.now(timezone.utc))


def get_lineups(seasons: list[Season]) -> tuple[list[Lineups], bool]:
    """Lineups for the given seasons (fetching any not cached yet), and whether ESPN failed."""
    espn_error = False
    try:
        for season in seasons:
            cached = _lineup_cache.get(season.year)
            stale = (
                season.in_progress
                and cached is not None
                and datetime.now(timezone.utc) - cached.fetched_at > CURRENT_SEASON_MAX_AGE
            )
            if cached is None or stale:
                _lineup_cache[season.year] = fetch_lineups(season)
    except Exception as exc:
        log.warning("ESPN lineup fetch failed: %s", type(exc).__name__)
        espn_error = True
    return [_lineup_cache[s.year] for s in seasons if s.year in _lineup_cache], espn_error


def select_seasons(seasons: list[Season], choice: str | None) -> tuple[list[str], str, list[Season]]:
    """The season dropdown: (years newest first, selected year or "all", seasons to show)."""
    years = [str(s.year) for s in reversed(seasons)]
    # ?season=<year> or ?season=all; anything else shows the current season.
    selected = choice if choice == "all" or choice in years else (years[0] if years else "all")
    shown = seasons if selected == "all" else [s for s in seasons if str(s.year) == selected]
    return years, selected, shown


def get_seasons() -> tuple[list[Season], bool]:
    """Every season the league has, oldest first, and whether ESPN failed this time."""
    espn_error = False
    year = current_season_year(date.today())
    try:
        cached = _cache.get(year)
        if cached is None or datetime.now(timezone.utc) - cached.fetched_at > CURRENT_SEASON_MAX_AGE:
            _cache[year] = fetch_season(year)
        for past in _cache[year].previous_seasons:
            if past not in _cache:
                _cache[past] = fetch_season(past)
    except Exception as exc:
        # The library's exception text never contains the cookies; don't log request details.
        log.warning("ESPN fetch failed: %s", type(exc).__name__)
        espn_error = True
    return [_cache[y] for y in sorted(_cache)], espn_error

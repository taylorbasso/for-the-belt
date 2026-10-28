"""Read league data from ESPN's unofficial fantasy API (read-only), with an in-memory cache.

Completed seasons never change, so each is fetched once per process. The current season is
re-fetched when its copy is more than 15 minutes old. If ESPN fails, callers get whatever is
cached plus an error flag.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from espn_api.football import League

log = logging.getLogger(__name__)

CURRENT_SEASON_MAX_AGE = timedelta(minutes=15)


@dataclass(frozen=True)
class ManagerSeason:
    year: int
    member_id: str
    name: str
    wins: int
    losses: int
    ties: int
    points_for: float
    points_against: float
    final_rank: int  # 0 while the season is in progress


@dataclass(frozen=True)
class Season:
    year: int
    managers: list[ManagerSeason]
    in_progress: bool
    previous_seasons: list[int]
    fetched_at: datetime


_cache: dict[int, Season] = {}


def current_season_year(today: date) -> int:
    """NFL seasons run September to early January; between seasons, the last one is current."""
    return today.year if today.month >= 9 else today.year - 1


def fetch_season(year: int) -> Season:
    league = League(
        league_id=int(os.environ["ESPN_LEAGUE_ID"]),
        year=year,
        espn_s2=os.environ["ESPN_S2"],
        swid=os.environ["ESPN_SWID"],
        fetch_league=False,
    )
    data: dict[str, Any] = league.espn_request.league_get(params={"view": "mTeam"})
    members = {m["id"]: m for m in data.get("members", [])}

    managers = []
    for team in data["teams"]:
        member = members.get(team.get("primaryOwner"))
        if member:
            member_id = member["id"]
            name = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
        else:
            member_id = name = team.get("name", f"Team {team['id']}")
        record = team["record"]["overall"]
        managers.append(
            ManagerSeason(
                year=year,
                member_id=member_id,
                name=name or member_id,
                wins=record["wins"],
                losses=record["losses"],
                ties=record["ties"],
                points_for=record["pointsFor"],
                points_against=record["pointsAgainst"],
                final_rank=team.get("rankCalculatedFinal") or 0,
            )
        )

    status = data["status"]
    return Season(
        year=year,
        managers=managers,
        in_progress=status["latestScoringPeriod"] <= status["finalScoringPeriod"],
        previous_seasons=list(status.get("previousSeasons", [])),
        fetched_at=datetime.now(timezone.utc),
    )


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

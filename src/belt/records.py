"""Historical Records tab: regular-season records per manager, for one season or all time."""

from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from flask import Blueprint, render_template, request

from belt import espn
from belt.espn import Season

bp = Blueprint("records", __name__)

LEAGUE_TZ = ZoneInfo("America/Denver")


@dataclass
class AllTimeRecord:
    member_id: str
    name: str
    seasons: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    titles: int = 0
    shotguns: int = 0

    @property
    def win_pct(self) -> float:
        games = self.wins + self.losses + self.ties
        return (self.wins + self.ties / 2) / games if games else 0.0


def all_time_records(seasons: list[Season]) -> list[AllTimeRecord]:
    """One row per ESPN member, ranked by win %, then points for."""
    rows: dict[str, AllTimeRecord] = {}
    for season in sorted(seasons, key=lambda s: s.year):
        for m in season.managers:
            row = rows.setdefault(m.member_id, AllTimeRecord(m.member_id, m.name))
            row.name = m.name  # latest season wins, since seasons are in order
            row.seasons += 1
            row.wins += m.wins
            row.losses += m.losses
            row.ties += m.ties
            row.points_for += m.points_for
            row.points_against += m.points_against
            if m.final_rank == 1:
                row.titles += 1
            row.shotguns += m.shotguns
    return sorted(rows.values(), key=lambda r: (r.win_pct, r.points_for), reverse=True)


@bp.route("/records")
def index() -> str:
    seasons, espn_error = espn.get_seasons()
    current = seasons[-1] if seasons else None
    years = [str(s.year) for s in reversed(seasons)]  # newest first
    # ?season=<year> or ?season=all; anything else shows the current season.
    selected = request.args.get("season")
    if selected != "all" and selected not in years:
        selected = years[0] if years else "all"
    shown = seasons if selected == "all" else [s for s in seasons if str(s.year) == selected]
    return render_template(
        "records.html",
        rows=all_time_records(shown),
        years=years,
        selected=selected,
        in_progress=current is not None and current.in_progress and current in shown,
        current=current,
        updated=current.fetched_at.astimezone(LEAGUE_TZ) if current else None,
        espn_error=espn_error,
    )

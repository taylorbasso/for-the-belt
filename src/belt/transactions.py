"""Transactions tab: pickups, drops, trades, lineup moves and IR moves per manager."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, render_template, request

from belt import espn
from belt.espn import Season
from belt.records import LEAGUE_TZ

bp = Blueprint("transactions", __name__)


@dataclass
class ManagerMoves:
    member_id: str
    name: str
    pickups: int = 0
    drops: int = 0
    trades: int = 0
    lineup_moves: int = 0
    ir_moves: int = 0


def all_moves(seasons: list[Season]) -> list[ManagerMoves]:
    """One row per ESPN member, most pickups first."""
    rows: dict[str, ManagerMoves] = {}
    for season in sorted(seasons, key=lambda s: s.year):
        for m in season.managers:
            row = rows.setdefault(m.member_id, ManagerMoves(m.member_id, m.name))
            row.name = m.name  # latest season wins, since seasons are in order
            row.pickups += m.pickups
            row.drops += m.drops
            row.trades += m.trades
            row.lineup_moves += m.lineup_moves
            row.ir_moves += m.ir_moves
    return sorted(rows.values(), key=lambda r: (-r.pickups, r.name))


@bp.route("/transactions")
def index() -> str:
    seasons, espn_error = espn.get_seasons()
    current = seasons[-1] if seasons else None
    years, selected, shown = espn.select_seasons(seasons, request.args.get("season"))
    return render_template(
        "transactions.html",
        rows=all_moves(shown),
        years=years,
        selected=selected,
        in_progress=current is not None and current.in_progress and current in shown,
        current=current,
        updated=current.fetched_at.astimezone(LEAGUE_TZ) if current else None,
        espn_error=espn_error,
    )

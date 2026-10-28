"""Bench tab: how close each manager's lineups came to the best lineup, in hindsight."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, render_template, request

from belt import espn
from belt.espn import BENCH, IR, Lineups, Player, Season
from belt.records import LEAGUE_TZ

bp = Blueprint("bench", __name__)


def best_lineup(players: list[Player], slot_counts: dict[int, int]) -> tuple[float, list[Player]]:
    """The highest score the roster could have started, and who'd start.

    Fills the most restrictive slots first (QB, K, D/ST before FLEX), each with the best
    eligible player left. FLEX takes a superset of the positions it overlaps, so this is optimal.
    """
    candidates = [p for p in players if p.slot != IR]
    slots = [slot for slot, n in slot_counts.items() for _ in range(n)]
    slots.sort(key=lambda slot: sum(slot in p.eligible for p in candidates))
    chosen: list[Player] = []
    for slot in slots:
        eligible = [p for p in candidates if slot in p.eligible and p not in chosen]
        if eligible:
            chosen.append(max(eligible, key=lambda p: p.points))
    return sum(p.points for p in chosen), chosen


def costliest_swap(players: list[Player], chosen: list[Player]) -> tuple[Player, Player] | None:
    """The (benched, started) pair with the biggest point gap: a benched player who belonged in
    the best lineup, and a starter who didn't whose slot he could have taken."""
    benched = [p for p in players if p.slot == BENCH and p in chosen]
    starters = [p for p in players if p.slot not in (BENCH, IR) and p not in chosen]
    pairs = [(b, s) for b in benched for s in starters if s.slot in b.eligible]
    return max(pairs, key=lambda pair: pair[0].points - pair[1].points, default=None)


@dataclass
class ManagerWeek:
    year: int
    week: int
    team_id: int
    member_id: str
    started: float
    best: float
    swap: tuple[Player, Player] | None

    @property
    def left(self) -> float:
        return self.best - self.started


def manager_weeks(season: Season, lineups: Lineups) -> list[ManagerWeek]:
    owners = {m.team_id: m.member_id for m in season.managers}
    weeks = []
    for tw in lineups.team_weeks:
        best, chosen = best_lineup(tw.players, lineups.slot_counts)
        started = sum(p.points for p in tw.players if p.slot not in (BENCH, IR))
        weeks.append(ManagerWeek(
            season.year, tw.week, tw.team_id, owners.get(tw.team_id, str(tw.team_id)),
            started, best, costliest_swap(tw.players, chosen),
        ))
    return weeks


def lineup_losses(lineups: Lineups, weeks: list[ManagerWeek]) -> dict[str, int]:
    """Per member: losses where their best possible score would have beaten the winner's score."""
    by_team_week = {(w.team_id, w.week): w for w in weeks}
    losses: dict[str, int] = {}
    for m in lineups.matchups:
        loser_weeks = [by_team_week[(m.loser_id, wk)] for wk in m.weeks if (m.loser_id, wk) in by_team_week]
        if loser_weeks and sum(w.best for w in loser_weeks) > m.winner_points:
            member_id = loser_weeks[0].member_id
            losses[member_id] = losses.get(member_id, 0) + 1
    return losses


@dataclass
class BenchRecord:
    member_id: str
    name: str
    started: float = 0.0
    best: float = 0.0
    weeks: int = 0
    lineup_losses: int = 0
    worst: ManagerWeek | None = None

    @property
    def lineup_pct(self) -> float:
        return self.started / self.best if self.best else 1.0

    @property
    def bench_per_week(self) -> float:
        return (self.best - self.started) / self.weeks if self.weeks else 0.0


def bench_records(pairs: list[tuple[Season, Lineups]]) -> list[BenchRecord]:
    """One row per ESPN member over the given seasons, most points left on the bench first."""
    rows: dict[str, BenchRecord] = {}
    for season, lineups in sorted(pairs, key=lambda pair: pair[0].year):
        names = {m.member_id: m.name for m in season.managers}
        weeks = manager_weeks(season, lineups)
        for w in weeks:
            row = rows.setdefault(w.member_id, BenchRecord(w.member_id, names.get(w.member_id, w.member_id)))
            row.name = names.get(w.member_id, row.name)  # latest season wins
            row.started += w.started
            row.best += w.best
            row.weeks += 1
            if w.left > 0.005 and (row.worst is None or w.left > row.worst.left):
                row.worst = w
        for member_id, n in lineup_losses(lineups, weeks).items():
            rows[member_id].lineup_losses += n
    return sorted(rows.values(), key=lambda r: r.bench_per_week, reverse=True)


@bp.route("/bench")
def index() -> str:
    seasons, espn_error = espn.get_seasons()
    current = seasons[-1] if seasons else None
    years, selected, shown = espn.select_seasons(seasons, request.args.get("season"))
    lineups, lineup_error = espn.get_lineups(shown)
    by_year = {lu.year: lu for lu in lineups}
    pairs = [(s, by_year[s.year]) for s in shown if s.year in by_year]
    rows = bench_records(pairs)
    worst = [r for r in rows if r.worst]
    return render_template(
        "bench.html",
        rows=rows,
        shame=max(worst, key=lambda r: r.worst.left, default=None),
        years=years,
        selected=selected,
        in_progress=current is not None and current.in_progress and current in shown,
        current=current,
        updated=current.fetched_at.astimezone(LEAGUE_TZ) if current else None,
        espn_error=espn_error or lineup_error,
    )

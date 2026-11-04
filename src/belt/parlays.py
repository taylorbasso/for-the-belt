"""Parlays tab: the weekly loser parlay, and who keeps busting it.

Each week the lowest scorer (LSP) puts $10 on a parlay in a category they pick, and every
member adds one leg. The LM records each week by hand in data/parlays.json (see CLAUDE.md).
Nothing here reads ESPN.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from flask import Blueprint, render_template

bp = Blueprint("parlays", __name__)

PARLAYS = Path(__file__).parent / "data" / "parlays.json"


@dataclass(frozen=True)
class Leg:
    member: str
    pick: str
    odds: int | None  # American odds, e.g. -150 or 240
    result: str | None  # "W", "L", or None until graded


@dataclass(frozen=True)
class Parlay:
    season: int
    week: int  # NFL week of the games bet on
    lsp: str
    category: str
    payout: float | None
    legs: list[Leg] = field(default_factory=list)


def load_parlays(path: Path = PARLAYS) -> list[Parlay]:
    """Every recorded parlay, newest first."""
    data = json.loads(path.read_text())
    parlays = [
        Parlay(
            season=p["season"],
            week=p["week"],
            lsp=p["lsp"],
            category=p["category"],
            payout=p.get("payout"),
            legs=[Leg(l["member"], l["pick"], l.get("odds"), l.get("result")) for l in p["legs"]],
        )
        for p in data["parlays"]
    ]
    return sorted(parlays, key=lambda p: (p.season, p.week), reverse=True)


def result(p: Parlay) -> str:
    """"busted" if any leg lost, "hit" if every leg won, else "pending"."""
    results = [leg.result for leg in p.legs]
    if "L" in results:
        return "busted"
    if results and all(r == "W" for r in results):
        return "hit"
    return "pending"


def sole_loser(p: Parlay) -> str | None:
    """The member whose leg was the only loss, once every leg is graded."""
    if any(leg.result is None for leg in p.legs):
        return None
    losers = [leg.member for leg in p.legs if leg.result == "L"]
    return losers[0] if len(losers) == 1 else None


def implied(odds: int) -> float:
    """The chance American odds imply: -200 is 2/3, +100 is 1/2, +150 is 0.4."""
    return -odds / (-odds + 100) if odds < 0 else 100 / (odds + 100)


@dataclass
class MemberStats:
    name: str
    wins: int = 0
    losses: int = 0
    kills: int = 0  # parlays where theirs was the only losing leg
    implied_sum: float = 0.0
    implied_n: int = 0

    @property
    def hit_rate(self) -> float | None:
        graded = self.wins + self.losses
        return self.wins / graded if graded else None

    @property
    def expected_rate(self) -> float | None:
        """How often the odds said their graded legs would hit."""
        return self.implied_sum / self.implied_n if self.implied_n else None


def member_stats(parlays: list[Parlay]) -> list[MemberStats]:
    """One row per member, worst picker first: most kills, then lowest hit rate."""
    rows: dict[str, MemberStats] = {}
    for p in parlays:
        for leg in p.legs:
            row = rows.setdefault(leg.member, MemberStats(leg.member))
            if leg.result is None:
                continue
            if leg.result == "W":
                row.wins += 1
            else:
                row.losses += 1
            if leg.odds is not None:
                row.implied_sum += implied(leg.odds)
                row.implied_n += 1
        killer = sole_loser(p)
        if killer is not None:
            rows[killer].kills += 1

    def rank(r: MemberStats) -> tuple:
        return (-r.kills, r.hit_rate is None, r.hit_rate or 0.0, r.name)

    return sorted(rows.values(), key=rank)


@bp.route("/parlays")
def index() -> str:
    parlays = load_parlays(PARLAYS)
    weeks = [(p, result(p), sole_loser(p)) for p in parlays]
    settled = [(p, r) for p, r, _ in weeks if r != "pending"]
    hits = [p for p, r in settled if r == "hit"]
    return render_template(
        "parlays.html",
        stats=member_stats(parlays),
        weeks=weeks,
        settled=len(settled),
        hits=len(hits),
        paid=sum(p.payout for p in hits if p.payout),
        many_seasons=len({p.season for p in parlays}) > 1,
    )

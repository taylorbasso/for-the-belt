import json

import pytest

from belt.app import create_app
from belt.parlays import Leg, Parlay, implied, load_parlays, member_stats, result, sole_loser


def parlay(*legs, week=10, season=2026, payout=None):
    """legs: (member, result) or (member, result, odds)."""
    return Parlay(season, week, "LSP", "Anything", payout,
                  [Leg(l[0], "pick", l[2] if len(l) > 2 else None, l[1]) for l in legs])


def by_name(rows):
    return {r.name: r for r in rows}


def test_record_and_hit_rate():
    a = by_name(member_stats([
        parlay(("A", "W")), parlay(("A", "L")), parlay(("A", "W")), parlay(("A", "W")),
    ]))["A"]
    assert (a.wins, a.losses) == (3, 1)
    assert a.hit_rate == 0.75


def test_only_losing_leg_gets_the_kill():
    p = parlay(("A", "L"), *[(m, "W") for m in "BCDEFGH"])
    assert sole_loser(p) == "A"
    rows = by_name(member_stats([p]))
    assert rows["A"].kills == 1
    assert all(rows[m].kills == 0 for m in "BCDEFGH")


def test_two_losses_means_no_kill():
    p = parlay(("A", "L"), ("B", "L"), ("C", "W"))
    assert sole_loser(p) is None
    rows = by_name(member_stats([p]))
    assert (rows["A"].kills, rows["A"].losses) == (0, 1)
    assert (rows["B"].kills, rows["B"].losses) == (0, 1)


def test_no_kill_until_every_leg_is_graded():
    p = parlay(("A", "L"), ("B", "W"), ("C", None))
    assert sole_loser(p) is None
    assert result(p) == "busted"


def test_implied_odds():
    assert implied(-200) == pytest.approx(2 / 3)
    assert implied(100) == pytest.approx(0.5)
    assert implied(150) == pytest.approx(0.4)
    assert implied(-110) == pytest.approx(110 / 210)


def test_expected_rate_averages_graded_legs_and_skips_missing_odds():
    a = by_name(member_stats([
        parlay(("A", "W", -200)), parlay(("A", "L", 100)),
        parlay(("A", "W")),          # no odds: counts in the record only
        parlay(("A", None, 500)),    # not graded: counts nowhere
    ]))["A"]
    assert a.expected_rate == pytest.approx((2 / 3 + 0.5) / 2)
    assert (a.wins, a.losses) == (2, 1)


def test_ungraded_member_shows_with_no_rates_and_sorts_last():
    rows = member_stats([parlay(("A", "W"), ("New", None))])
    assert [r.name for r in rows] == ["A", "New"]
    new = rows[-1]
    assert (new.wins, new.losses, new.hit_rate, new.expected_rate) == (0, 0, None, None)


def test_ranked_by_kills_then_lowest_hit_rate():
    rows = member_stats([
        parlay(("Killer", "L"), ("Good", "W"), ("Meh", "W")),
        parlay(("Killer", "W"), ("Good", "W"), ("Meh", "L"), ("Bad", "L")),
        parlay(("Bad", "L"), ("Good", "W"), ("Meh", "L")),
    ])
    assert [r.name for r in rows] == ["Killer", "Bad", "Meh", "Good"]


def test_result():
    assert result(parlay(("A", "W"), ("B", "W"))) == "hit"
    assert result(parlay(("A", "W"), ("B", "L"))) == "busted"
    assert result(parlay(("A", "W"), ("B", None))) == "pending"


def test_load_parlays_newest_first(tmp_path):
    path = tmp_path / "parlays.json"
    path.write_text(json.dumps({"parlays": [
        {"season": 2026, "week": 9, "lsp": "A", "category": "ML", "payout": None,
         "legs": [{"member": "A", "pick": "Chiefs ML", "odds": -150, "result": "W"}]},
        {"season": 2026, "week": 11, "lsp": "B", "category": "TDs", "payout": 412.5,
         "legs": [{"member": "B", "pick": "Bijan anytime TD", "odds": 120, "result": None}]},
    ]}))
    parlays = load_parlays(path)
    assert [p.week for p in parlays] == [11, 9]
    assert parlays[0].legs[0] == Leg("B", "Bijan anytime TD", 120, None)


def test_page_renders_empty_and_with_data(tmp_path, monkeypatch):
    client = create_app().test_client()
    import belt.parlays as mod

    path = tmp_path / "parlays.json"
    path.write_text(json.dumps({"parlays": []}))
    monkeypatch.setattr(mod, "PARLAYS", path)
    assert "No parlays recorded yet" in client.get("/parlays").get_data(as_text=True)

    path.write_text(json.dumps({"parlays": [
        {"season": 2026, "week": 10, "lsp": "A", "category": "NFL ML only", "payout": None,
         "legs": [{"member": "A", "pick": "Chiefs ML", "odds": -150, "result": "L"},
                  {"member": "B", "pick": "Bills ML", "odds": 130, "result": "W"}]},
    ]}))
    page = client.get("/parlays").get_data(as_text=True)
    assert "NFL ML only" in page and "Chiefs ML" in page and "killed it" in page

from belt import espn
from belt.app import create_app
from belt.transactions import all_moves
from test_records import manager, season


def test_sums_moves_across_seasons_under_latest_name():
    [row] = all_moves([
        season(2024, manager(2024, "a", "Old", 7, 7, pickups=10, drops=11, trades=1, lineup_moves=50, ir_moves=2)),
        season(2025, manager(2025, "a", "New", 7, 7, pickups=5, drops=4, trades=2, lineup_moves=30, ir_moves=1)),
    ])
    assert (row.name, row.pickups, row.drops, row.trades, row.lineup_moves, row.ir_moves) == (
        "New", 15, 15, 3, 80, 3)


def test_ranked_by_pickups():
    rows = all_moves([season(
        2025,
        manager(2025, "few", "Few", 7, 7, pickups=3),
        manager(2025, "many", "Many", 7, 7, pickups=30),
    )])
    assert [r.member_id for r in rows] == ["many", "few"]


def test_season_picker_defaults_to_current_season(monkeypatch):
    seasons = [
        season(2025, manager(2025, "a", "A", 7, 7, pickups=41)),
        season(2026, manager(2026, "a", "A", 3, 4, pickups=13)),
    ]
    monkeypatch.setattr(espn, "get_seasons", lambda: (seasons, False))
    client = create_app().test_client()

    def page(query=""):
        return client.get("/transactions" + query).get_data(as_text=True)

    assert "<td>13</td>" in page()
    assert "<td>41</td>" in page("?season=2025")
    assert "<td>54</td>" in page("?season=all")

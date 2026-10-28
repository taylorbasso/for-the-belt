from datetime import datetime, timezone

from belt.espn import ManagerSeason, Season
from belt.records import all_time_records


def manager(year, member_id, name, w, l, t=0, pf=100.0, pa=100.0, rank=0):
    return ManagerSeason(year, member_id, name, w, l, t, pf, pa, rank)


def season(year, *managers):
    return Season(year, list(managers), False, [], datetime.now(timezone.utc))


def by_id(rows):
    return {r.member_id: r for r in rows}


def test_combines_renamed_teams_under_one_member_with_latest_name():
    rows = all_time_records([
        season(2023, manager(2023, "a", "Old Name", 8, 6, rank=1)),
        season(2024, manager(2024, "a", "New Name", 7, 7, rank=3)),
    ])
    assert len(rows) == 1
    a = rows[0]
    assert (a.name, a.seasons, a.wins, a.losses) == ("New Name", 2, 15, 13)


def test_tie_counts_as_half_a_win():
    [row] = all_time_records([season(2024, manager(2024, "a", "A", 1, 1, 2))])
    assert row.win_pct == 0.5


def test_equal_win_pct_ranked_by_points_for():
    rows = all_time_records([season(
        2024,
        manager(2024, "low", "Low", 5, 5, pf=900.0),
        manager(2024, "high", "High", 5, 5, pf=1000.0),
    )])
    assert [r.member_id for r in rows] == ["high", "low"]


def test_titles_only_count_first_place_finishes():
    rows = by_id(all_time_records([
        season(2023, manager(2023, "a", "A", 9, 5, rank=1), manager(2023, "b", "B", 5, 9, rank=2)),
        season(2024, manager(2024, "a", "A", 3, 2, rank=0), manager(2024, "b", "B", 2, 3, rank=0)),
    ]))
    assert rows["a"].titles == 1
    assert rows["b"].titles == 0


def test_manager_with_fewer_seasons():
    rows = by_id(all_time_records([
        season(2023, manager(2023, "a", "A", 7, 7)),
        season(2024, manager(2024, "a", "A", 7, 7), manager(2024, "b", "B", 7, 7)),
    ]))
    assert rows["a"].seasons == 2
    assert rows["b"].seasons == 1

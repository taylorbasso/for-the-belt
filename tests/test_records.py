from datetime import datetime, timezone

from belt import espn
from belt.app import create_app
from belt.espn import ManagerSeason, Season, shotguns_by_team
from belt.records import all_time_records


def manager(year, member_id, name, w, l, t=0, pf=100.0, pa=100.0, rank=0, shotguns=0):
    return ManagerSeason(year, member_id, name, w, l, t, pf, pa, rank, shotguns)


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


def test_shotguns_sum_across_seasons():
    [row] = all_time_records([
        season(2023, manager(2023, "a", "A", 7, 7, shotguns=3)),
        season(2024, manager(2024, "a", "A", 7, 7, shotguns=2)),
    ])
    assert row.shotguns == 5


def side(team_id, weeks):
    return {"teamId": team_id, "pointsByScoringPeriod": {str(w): p for w, p in weeks.items()}}


def test_shotguns_count_lowest_score_per_completed_week():
    schedule = [
        {"home": side(1, {1: 80.0}), "away": side(2, {1: 100.0})},
        {"home": side(3, {1: 90.0}), "away": side(4, {1: 95.0})},
        # A two-week playoff matchup is scored week by week.
        {"home": side(1, {2: 120.0, 3: 60.0}), "away": side(2, {2: 70.0, 3: 110.0})},
        {"home": side(3, {2: 70.0, 3: 100.0}), "away": side(4, {2: 90.0, 3: 105.0})},
        # Week 4 hasn't finished yet.
        {"home": side(1, {4: 0.0}), "away": side(2, {4: 0.0})},
    ]
    counts = shotguns_by_team(schedule, latest_scoring_period=4)
    # Week 1: team 1. Week 2: teams 2 and 3 tie. Week 3: team 1.
    assert counts == {1: 2, 2: 1, 3: 1}


def test_shotguns_include_teams_without_an_opponent():
    schedule = [{"home": side(1, {1: 50.0})}, {"home": side(2, {1: 90.0}), "away": side(3, {1: 80.0})}]
    assert shotguns_by_team(schedule, latest_scoring_period=2) == {1: 1}


def test_season_picker_defaults_to_current_season(monkeypatch):
    seasons = [
        season(2025, manager(2025, "a", "A", 9, 5, rank=1)),
        season(2026, manager(2026, "a", "A", 3, 4)),
    ]
    monkeypatch.setattr(espn, "get_seasons", lambda: (seasons, False))
    client = create_app().test_client()

    def page(query=""):
        return client.get("/records" + query).get_data(as_text=True)

    assert "3-4-0" in page()  # current season by default
    assert "9-5-0" in page("?season=2025")
    assert "12-9-0" in page("?season=all")
    assert "3-4-0" in page("?season=1999")  # unknown year falls back to current

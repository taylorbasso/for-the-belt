from datetime import datetime, timezone

from belt.bench import bench_records, best_lineup, costliest_swap, lineup_losses, manager_weeks
from belt.espn import Lineups, Matchup, Player, Season, TeamWeek
from test_records import manager

QB, RB, WR, TE, FLEX, BENCH, IR = 0, 2, 4, 6, 23, 20, 21
SLOTS = {QB: 1, RB: 1, WR: 1, FLEX: 1}
ELIGIBLE = {
    "QB": frozenset({QB, BENCH, IR}),
    "RB": frozenset({RB, FLEX, BENCH, IR}),
    "WR": frozenset({WR, FLEX, BENCH, IR}),
    "TE": frozenset({TE, FLEX, BENCH, IR}),
}


def player(name, pos, slot, points):
    return Player(name, slot, points, ELIGIBLE[pos])


def roster(*players):
    return list(players)


def left(players):
    best, _ = best_lineup(players, SLOTS)
    return round(best - sum(p.points for p in players if p.slot not in (BENCH, IR)), 2)


def test_benched_wr_who_outscored_the_starter():
    players = roster(
        player("Q", "QB", QB, 20), player("R", "RB", RB, 10), player("W1", "WR", WR, 6),
        player("F", "RB", FLEX, 8), player("W2", "WR", BENCH, 25),
    )
    assert left(players) == 19


def test_good_bench_that_scored_less_costs_nothing():
    players = roster(
        player("Q", "QB", QB, 20), player("R", "RB", RB, 10), player("W", "WR", WR, 15),
        player("F", "RB", FLEX, 12), player("B1", "WR", BENCH, 9), player("B2", "QB", BENCH, 18),
    )
    assert left(players) == 0


def test_bench_rb_takes_flex_from_a_te():
    players = roster(
        player("Q", "QB", QB, 20), player("R", "RB", RB, 10), player("W", "WR", WR, 15),
        player("T", "TE", FLEX, 3), player("R2", "RB", BENCH, 9),
    )
    assert left(players) == 6


def test_ir_players_never_count():
    players = roster(
        player("Q", "QB", QB, 20), player("R", "RB", RB, 10), player("W", "WR", WR, 15),
        player("F", "RB", FLEX, 5), player("Hurt", "RB", IR, 40),
    )
    assert left(players) == 0


def test_costliest_swap_only_pairs_eligible_slots():
    q2 = player("Q2", "QB", BENCH, 35)
    players = roster(
        player("Q", "QB", QB, 10), player("R", "RB", RB, 10), player("W", "WR", WR, 1),
        player("F", "RB", FLEX, 8), q2,
    )
    _, chosen = best_lineup(players, SLOTS)
    bench, starter = costliest_swap(players, chosen)
    assert (bench.name, starter.name) == ("Q2", "Q")  # not the 1-point WR


def season_with(lineup_weeks, matchups):
    season = Season(2025, [manager(2025, "a", "A", 7, 7, team_id=1), manager(2025, "b", "B", 7, 7, team_id=2)],
                    False, [], datetime.now(timezone.utc))
    return season, Lineups(2025, SLOTS, lineup_weeks, matchups, datetime.now(timezone.utc))


def week(team_id, wk, started_wr, bench_wr):
    return TeamWeek(wk, team_id, [
        player("Q", "QB", QB, 10), player("R", "RB", RB, 10), player("F", "RB", FLEX, 10),
        player("W", "WR", WR, started_wr), player("B", "WR", BENCH, bench_wr),
    ])


def test_two_week_playoff_loss_uses_both_weeks_best():
    # Team 1 started 40 + 40 = 80 vs the winner's 95; best was 45 + 55 = 100.
    season, lineups = season_with(
        [week(1, 15, 10, 15), week(1, 16, 10, 25)], [Matchup([15, 16], 2, 1, 95.0)])
    assert lineup_losses(lineups, manager_weeks(season, lineups)) == {"a": 1}


def test_loss_the_best_lineup_still_loses_isnt_counted():
    season, lineups = season_with([week(1, 3, 10, 15)], [Matchup([3], 2, 1, 120.0)])
    assert lineup_losses(lineups, manager_weeks(season, lineups)) == {}


def test_bench_records_group_by_member_and_pick_worst_week():
    season, lineups = season_with(
        [week(1, 1, 10, 15), week(1, 2, 10, 30), week(2, 1, 20, 5)], [Matchup([1], 2, 1, 200.0)])
    rows = {r.member_id: r for r in bench_records([(season, lineups)])}
    a = rows["a"]
    assert (a.weeks, round(a.bench_per_week, 2), a.worst.week, round(a.worst.left, 2)) == (2, 12.5, 2, 20)
    assert rows["b"].worst is None and rows["b"].lineup_pct == 1.0
    assert [r.member_id for r in bench_records([(season, lineups)])] == ["a", "b"]  # worst first

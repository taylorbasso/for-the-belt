# /// script
# requires-python = ">=3.10"
# dependencies = ["espn-api", "python-dotenv"]
# ///
"""Print all-time regular-season records for every manager in the league.

Usage: uv run scripts/lifetime_records.py
Reads ESPN_LEAGUE_ID, ESPN_S2, and ESPN_SWID from .env (see .env.example).
"""

import os
from collections import defaultdict

from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()
LEAGUE_ID = int(os.environ["ESPN_LEAGUE_ID"])
COOKIES = {"espn_s2": os.environ["ESPN_S2"], "swid": os.environ["ESPN_SWID"]}
YEAR = int(os.environ.get("ESPN_YEAR", 2026))


def owner_key(team):
    # Team names change every year; the ESPN member id is the stable identity.
    if team.owners:
        o = team.owners[0]
        name = f"{o.get('firstName', '')} {o.get('lastName', '')}".strip()
        return o["id"], name or o.get("displayName", team.team_name)
    return team.team_name, team.team_name


def main():
    current = League(league_id=LEAGUE_ID, year=YEAR, **COOKIES)
    seasons = sorted(current.previousSeasons) + [YEAR]
    print(f"Seasons found: {', '.join(map(str, seasons))}\n")

    totals = defaultdict(lambda: {"name": "", "w": 0, "l": 0, "t": 0, "pf": 0.0, "pa": 0.0,
                                  "seasons": 0, "titles": 0})
    for year in seasons:
        league = current if year == YEAR else League(league_id=LEAGUE_ID, year=year, **COOKIES)
        for team in league.teams:
            key, name = owner_key(team)
            row = totals[key]
            row["name"] = name
            row["w"] += team.wins
            row["l"] += team.losses
            row["t"] += team.ties
            row["pf"] += team.points_for
            row["pa"] += team.points_against
            row["seasons"] += 1
            if team.final_standing == 1:
                row["titles"] += 1

    rows = sorted(totals.values(),
                  key=lambda r: ((r["w"] + r["t"] / 2) / max(r["w"] + r["l"] + r["t"], 1), r["pf"]),
                  reverse=True)
    print(f"{'Manager':<24}{'Yrs':>4}{'W-L-T':>11}{'Win%':>7}{'PF':>10}{'PA':>10}{'Titles':>8}")
    for r in rows:
        games = r["w"] + r["l"] + r["t"]
        pct = (r["w"] + r["t"] / 2) / games if games else 0
        record = f"{r['w']}-{r['l']}-{r['t']}"
        print(f"{r['name'][:23]:<24}{r['seasons']:>4}{record:>11}{pct:>7.3f}"
              f"{r['pf']:>10.1f}{r['pa']:>10.1f}{r['titles']:>8}")
    print(f"\nRegular season only. {YEAR} is included and may be in progress.")


if __name__ == "__main__":
    main()

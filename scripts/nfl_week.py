#!/usr/bin/env python3
"""Print an NFL week's final scores and anytime-TD scorers, for grading parlay legs.

    python3 scripts/nfl_week.py 2026 8

Reads ESPN's public NFL scoreboard and box scores (no login). Passing TDs don't count as an
anytime TD; rushing, receiving, return and defensive TDs do. Not part of the app.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from urllib.request import urlopen

BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

# Box score categories and the stat key that holds that category's touchdowns.
TD_KEYS = {
    "rushing": "rushingTouchdowns",
    "receiving": "receivingTouchdowns",
    "kickReturns": "kickReturnTouchdowns",
    "puntReturns": "puntReturnTouchdowns",
    "interceptions": "interceptionTouchdowns",
    "defensive": "defensiveTouchdowns",
}


def get(url: str) -> dict:
    with urlopen(url, timeout=20) as resp:
        return json.load(resp)


def main(season: int, week: int) -> None:
    board = get(f"{BASE}/scoreboard?dates={season}&seasontype=2&week={week}")
    scorers: Counter[tuple[str, str]] = Counter()
    print(f"NFL {season} week {week}\n\nFinal scores")
    for event in board["events"]:
        comp = event["competitions"][0]
        status = event["status"]["type"]
        sides = sorted(comp["competitors"], key=lambda c: c["homeAway"] != "away")
        line = " at ".join(f"{c['team']['abbreviation']} {c.get('score', '')}" for c in sides)
        winner = next((c["team"]["abbreviation"] for c in sides if c.get("winner")), None)
        print(f"  {line}  ->  {winner + ' won' if winner else status['description']}")

        summary = get(f"{BASE}/summary?event={event['id']}")
        for team in summary.get("boxscore", {}).get("players", []):
            abbr = team["team"]["abbreviation"]
            for cat in team["statistics"]:
                key = TD_KEYS.get(cat["name"])
                if key not in cat.get("keys", []):
                    continue
                i = cat["keys"].index(key)
                for a in cat["athletes"]:
                    tds = int(a["stats"][i] or 0) if i < len(a["stats"]) else 0
                    if tds:
                        scorers[(a["athlete"]["displayName"], abbr)] += tds

    print("\nAnytime TD scorers")
    for (name, abbr), n in sorted(scorers.items()):
        print(f"  {name} ({abbr}){f' x{n}' if n > 1 else ''}")


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))

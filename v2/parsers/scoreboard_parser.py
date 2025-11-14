
import json
from pathlib import Path
from typing import List, Dict

def parse_scoreboard_data(cache_dir: Path, year: int, week: int) -> List[Dict]:
    """
    Parses the raw scoreboard JSON data from the cache and returns a list of matchups.
    """
    with open(cache_dir / f"scoreboard_{year}_w{week}.json", "r") as f:
        scoreboard_data = json.load(f)

    matchups = []
    for matchup_json in scoreboard_data["league"]["scoreboard"]["matchups"]:
        matchup = matchup_json["matchup"]
        teams = matchup["teams"]
        team1 = teams[0]["team"]
        team2 = teams[1]["team"]

        winner_team_key = matchup.get("winner_team_key")
        winner_team_id = None
        if winner_team_key:
            for team in [team1, team2]:
                if team["team_key"] == winner_team_key:
                    winner_team_id = team["team_id"]
                    break

        matchups.append({
            "week": matchup["week"],
            "team1_id": team1["team_id"],
            "team1_score": team1["team_points"]["total"],
            "team2_id": team2["team_id"],
            "team2_score": team2["team_points"]["total"],
            "winner_team_id": winner_team_id
        })

    return matchups

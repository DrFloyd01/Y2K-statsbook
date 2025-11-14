
import json
from pathlib import Path
from v2.models.league import League, Team, Player

def parse_league_data(cache_dir: Path, year: int, week: int) -> League:
    """
    Parses the raw JSON data from the cache and returns a League object.
    """
    # Load raw data from cache
    with open(cache_dir / f"settings_{year}.json", "r") as f:
        settings_data = json.load(f)

    with open(cache_dir / f"teams_{year}.json", "r") as f:
        teams_data = json.load(f)

    with open(cache_dir / f"rosters_{year}_w{week}.json", "r") as f:
        rosters_data = json.load(f)

    # Extract league-level data
    league_data = settings_data["league"]
    league = League(
        league_id=league_data["league_id"],
        name=league_data["name"],
        season=league_data["season"],
        teams=[]
    )

    # Parse teams and players
    for team_json in teams_data["league"]["teams"]:
        team_info = team_json["team"]
        team_id = team_info["team_id"]

        team_roster = []
        if str(team_id) in rosters_data:
            roster_json = rosters_data[str(team_id)]["team"]["roster"]
            if "players" in roster_json:
                for player_json in roster_json["players"]:
                    player_info = player_json["player"]
                    player = Player(
                        player_id=player_info["player_id"],
                        name=player_info["name"]["full"],
                        position=player_info["primary_position"],
                        nfl_team=player_info["editorial_team_abbr"]
                    )
                    team_roster.append(player)

        team = Team(
            team_id=team_id,
            manager_name=team_info["managers"]["manager"]["nickname"],
            roster=team_roster
        )
        league.teams.append(team)

    return league

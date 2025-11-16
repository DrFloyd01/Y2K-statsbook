
import json
from pathlib import Path
from v2.models.league import League, Team, Player

def _parse_roster_data(rosters_data: dict, team_id: int) -> list[Player]:
    """
    Parses the roster data for a single team.
    """
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
                    nfl_team=player_info["editorial_team_abbr"],
                    starting_status=(player_info["selected_position"]["position"] not in ("BN", "IR")),
                    actual_score=float(player_json["player"]["player_points"]["total"])
                )
                team_roster.append(player)
    return team_roster

def parse_league_data(cache_dir: Path, year: int, league: League):
    """
    Parses the raw JSON data from the cache and populates a League object.
    """
    # Load raw data from cache
    with open(cache_dir / f"settings_{year}.json", "r") as f:
        settings_data = json.load(f)

    with open(cache_dir / f"teams_{year}.json", "r") as f:
        teams_data = json.load(f)

    # Extract league-level data
    league_data = settings_data["league"]
    league.league_id = league_data["league_id"]
    league.name = league_data["name"]
    league.season = league_data["season"]

    # Parse teams and players
    for team_json in teams_data["league"]["teams"]:
        team_info = team_json["team"]
        team = Team(
            team_id=team_info["team_id"],
            manager_name=team_info["managers"]["manager"]["nickname"],
            roster=[]  # Initialize with an empty roster
        )
        league.teams.append(team)

def parse_weekly_rosters(league: League, cache_dir: Path, year: int, week: int):
    """
    Parses and updates the rosters for all teams in the league for a specific week.
    """
    roster_file = cache_dir / f"rosters_{year}_w{week}.json"
    if not roster_file.exists():
        return  # Skip if no roster data for this week

    with open(roster_file, "r") as f:
        rosters_data = json.load(f)

    for team in league.teams:
        team.roster = _parse_roster_data(rosters_data, team.team_id)

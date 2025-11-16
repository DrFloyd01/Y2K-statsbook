"""
Integrates multiple parsing functions to build a complete League object from cached data.
"""
import json
from pathlib import Path
from typing import Dict

from v2.models.league import League, Team, Matchup, PlayoffSettings
from v2.parsers.league_parser import parse_league_data
from v2.parsers.scoreboard_parser import parse_scoreboard_data

def load_league_from_cache(cache_dir: Path, year: int) -> League:
    """
    Builds a complete League object by parsing and integrating settings, teams,
    rosters, and weekly scoreboard data from the cache.

    Args:
        cache_dir: The path to the directory where API data is cached.
        year: The season year to load.

    Returns:
        A fully populated League object with teams and a complete schedule.
    """
    # 1. Create a new League object
    league = League(league_id="", season=year, name="", teams=[])

    # 2. Manually parse playoff settings and current week
    with open(cache_dir / f"settings_{year}.json", "r") as f:
        settings_data = json.load(f)
    playoff_start_week = settings_data["league"]["settings"]["playoff_start_week"]
    current_week = settings_data["league"]["current_week"]
    league.playoff_settings = PlayoffSettings(start_week=int(playoff_start_week))

    # 3. Iterate through all possible weeks up to the current week
    for week in range(1, current_week):
        # Skip weeks with no cached roster data
        roster_file = cache_dir / f"rosters_{year}_w{week}.json"
        if not roster_file.exists():
            continue

        # Parse the league data and populate the League object
        if not league.teams:
            parse_league_data(cache_dir, year, week, league)

        # Create a team_id -> Team object map for quick lookups
        team_map: Dict[int, Team] = {team.team_id: team for team in league.teams}

        scoreboard_file = cache_dir / f"scoreboard_{year}_w{week}.json"

        if not scoreboard_file.exists():
            continue # Skip weeks with no cached data

        # Parse the scoreboard data for the week
        matchup_dicts = parse_scoreboard_data(cache_dir, year, week)

        matchups_for_week = []
        for matchup_dict in matchup_dicts:
            team1 = team_map.get(matchup_dict["team1_id"])
            team2 = team_map.get(matchup_dict["team2_id"])

            # Ensure both teams were found in our map
            if not team1 or not team2:
                continue

            matchup = Matchup(
                week=week,
                team1=team1,
                team2=team2,
                team1_score=matchup_dict["team1_score"],
                team2_score=matchup_dict["team2_score"],
            )
            matchups_for_week.append(matchup)

        # Add the matchups to the correct schedule based on the week
        if week < league.playoff_settings.start_week:
            league.schedule.regular_season[week] = matchups_for_week
        else:
            league.schedule.playoffs[week] = matchups_for_week

    return league

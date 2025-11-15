
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

# --- Directory Setup ---
CACHE_DIR = Path("v2/api_cache")
CACHE_DIR.mkdir(exist_ok=True)
TARGET_SEASON = "2025"

def main():
    """
    Fetches sample data from the Yahoo Fantasy API and stores it as raw JSON.
    """
    logging.info("--- Starting API Data Fetch ---")

    with open("leagues.json", "r") as f:
        config = json.load(f)[TARGET_SEASON]

    query = YahooFantasySportsQuery(
        league_id=config["league_id"],
        game_code="nfl",
        game_id=config["game_id"]
    )
    json_query = YahooFantasySportsQuery(
        league_id=config["league_id"],
        game_code="nfl",
        game_id=config["game_id"],
        all_output_as_json_str=True
    )

    league_key = query.get_league_key()

    # We need to iterate through all completed weeks of the season to get the full schedule.
    # A full season is typically 17 weeks.
    for week in range(1, 18):
        logging.info(f"--- Fetching data for Week {week} ---")

        # We only need to fetch settings and teams once.
        if week == 1:
            # 1. Fetch League Settings
            logging.info(f"Fetching league settings for {TARGET_SEASON}...")
            settings_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/settings", [])
            settings_data = json.loads(settings_str)
            settings_file = CACHE_DIR / f"settings_{TARGET_SEASON}.json"
            with open(settings_file, "w") as f:
                json.dump(settings_data, f, indent=2)
            logging.info(f"✅ Saved league settings to {settings_file}")

            # 2. Fetch Teams
            logging.info(f"Fetching teams for {TARGET_SEASON}...")
            teams_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams", [])
            teams_data = json.loads(teams_str)
            teams_file = CACHE_DIR / f"teams_{TARGET_SEASON}.json"
            with open(teams_file, "w") as f:
                json.dump(teams_data, f, indent=2)
            logging.info(f"✅ Saved teams to {teams_file}")

        # 3. Fetch Scoreboard for the current week
        logging.info(f"Fetching scoreboard for Week {week}...")
        scoreboard_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/scoreboard;week={week}", [])
        scoreboard_data = json.loads(scoreboard_str)

        # Check if the scoreboard has matchups before saving
        if scoreboard_data.get("league", {}).get("scoreboard", {}).get("matchups"):
            scoreboard_file = CACHE_DIR / f"scoreboard_{TARGET_SEASON}_w{week}.json"
            with open(scoreboard_file, "w") as f:
                json.dump(scoreboard_data, f, indent=2)
            logging.info(f"✅ Saved scoreboard to {scoreboard_file}")
        else:
            logging.info(f"No matchups found for Week {week}. Skipping file save. This may indicate the week has not occurred yet.")
            # If we don't find matchups, we can assume we've reached the end of the completed weeks.
            break

    # 4. Fetch Rosters (only needed for one week to populate the team models)
    logging.info(f"--- Fetching final roster data ---")
    all_rosters = {}
    teams_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams", [])
    teams_data = json.loads(teams_str)
    if teams_data:
        for team_data in teams_data["league"]["teams"]:
            team = team_data['team']
            team_key = team["team_key"]
            team_id = team["team_id"]
            logging.info(f"  - Fetching roster for team {team_id}...")
            roster_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster;week=1", [])
            all_rosters[team_id] = json.loads(roster_str)
    rosters_file = CACHE_DIR / f"rosters_{TARGET_SEASON}_w1.json"
    with open(rosters_file, "w") as f:
        json.dump(all_rosters, f, indent=2)
    logging.info(f"✅ Saved all team rosters to {rosters_file}")

    logging.info("\n--- API Data Fetch Complete ---")

if __name__ == "__main__":
    main()

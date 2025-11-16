
import json
import logging
import os
from pathlib import Path
from yfpy.query import YahooFantasySportsQuery
from dotenv import load_dotenv

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(message)s')

# --- Directory Setup ---
CACHE_DIR = Path("v2/api_cache")
CACHE_DIR.mkdir(exist_ok=True)
TARGET_SEASON = "2025"

# Load environment variables from a local .env file (if present)
load_dotenv()

def main():
    """
    Fetches sample data from the Yahoo Fantasy API and stores it as raw JSON.
    """
    logging.info("--- Starting API Data Fetch ---")

    with open("leagues.json", "r") as f:
        config = json.load(f)[TARGET_SEASON]

    # --- Programmatic Authentication ---
    access_token_json = {
        "access_token": os.environ.get("YAHOO_ACCESS_TOKEN"),
        "consumer_key": os.environ.get("YAHOO_CONSUMER_KEY"),
        "consumer_secret": os.environ.get("YAHOO_CONSUMER_SECRET"),
        "guid": os.environ.get("YAHOO_GUID"),
        "refresh_token": os.environ.get("YAHOO_REFRESH_TOKEN"),
        "token_time": float(os.environ.get("YAHOO_TOKEN_TIME", 0)),
        "token_type": "bearer"
    }

    query = YahooFantasySportsQuery(
        league_id=config["league_id"],
        game_code="nfl",
        game_id=config["game_id"],
        yahoo_access_token_json=access_token_json
    )
    json_query = YahooFantasySportsQuery(
        league_id=config["league_id"],
        game_code="nfl",
        game_id=config["game_id"],
        yahoo_access_token_json=access_token_json,
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

    # 4. Fetch Rosters for each week
    logging.info(f"--- Fetching weekly roster data ---")
    teams_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/teams", [])
    teams_data = json.loads(teams_str)
    if teams_data:
        for week in range(1, 11):
            all_rosters = {}
            for team_data in teams_data["league"]["teams"]:
                team = team_data['team']
                team_key = team["team_key"]
                team_id = team["team_id"]
                logging.info(f"  - Fetching roster for team {team_id} for week {week}...")
                roster_str = json_query.query(f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster;week={week}/players/stats", [])
                all_rosters[team_id] = json.loads(roster_str)
            rosters_file = CACHE_DIR / f"rosters_{TARGET_SEASON}_w{week}.json"
            with open(rosters_file, "w") as f:
                json.dump(all_rosters, f, indent=2)
            logging.info(f"✅ Saved all team rosters for week {week} to {rosters_file}")

    logging.info("\n--- API Data Fetch Complete ---")

if __name__ == "__main__":
    main()

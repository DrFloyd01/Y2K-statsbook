import json
import logging
import os
import pickle
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

def cache_all_raw_data():
    """
    Connects to the API one last time to fetch all raw matchup data
    and save it to a local pickle file.
    """
    with open("leagues.json", "r") as f:
        all_leagues = json.load(f)

    # This dictionary will hold all our raw data
    # Structure: { "2018": { "1": [matchups], "2": [matchups]... } ... }
    complete_raw_data = {}

    for season, config in all_leagues.items():
        if not config.get("league_id"):
            continue
        
        logging.info(f"--- Fetching Season: {season} ---")
        complete_raw_data[season] = {}

        query = YahooFantasySportsQuery(
            league_id=config["league_id"], game_code="nfl", game_id=config["game_id"],
            yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
            env_file_location=Path("."), save_token_data_to_env_file=True
        )

        # <<< FIX IS HERE: Fetch and store the settings object directly >>>
        settings = query.get_league_settings()
        complete_raw_data[season] = {
            "settings": settings,
            "weeks": {}
        }
        
        playoff_start_week = int(settings.playoff_start_week)
        num_playoff_teams = int(settings.num_playoff_teams)
        total_weeks = (playoff_start_week + 2) if num_playoff_teams >= 6 else (playoff_start_week + 1)

        for week in range(1, total_weeks + 1):
            logging.info(f"Fetching raw data for {season}, Week {week}...")
            # <<< FIX IS HERE: Use the better API call for playoff weeks >>>
            if week >= playoff_start_week:
                # This call returns richer matchup objects with correct playoff flags
                scoreboard = query.get_league_scoreboard_by_week(week)
                matchups = scoreboard.matchups
            else:
                # Regular season call is fine
                matchups = query.get_league_matchups_by_week(week)
            if matchups and matchups[0].status == "postevent":
                # Store weekly matchups inside the 'weeks' dictionary
                complete_raw_data[season]["weeks"][str(week)] = matchups
            else:
                logging.info(f"Skipping Week {week} (not yet played).")

    # Save the entire collection of raw data to a single file
    with open("raw_api_cache.pkl", "wb") as f:
        pickle.dump(complete_raw_data, f)
        
    logging.info("\n✅ Success! All raw API data saved to raw_api_cache.pkl")

if __name__ == "__main__":
    cache_all_raw_data()
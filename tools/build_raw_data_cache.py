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

# --- Directory Setup ---
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

def update_raw_data_cache(season, week):
    """
    Efficiently updates the raw_api_cache.pkl with a single week's data
    from the weekly cache files.
    """
    logging.info(f"Updating raw_api_cache.pkl with data for {season}, Week {week}...")
    
    raw_cache_file = CACHE_DIR / "raw_api_cache.pkl"
    weekly_cache_file = CACHE_DIR / f"week_{week}_matchups.pkl"

    if not weekly_cache_file.exists():
        logging.error(f"ERROR: Cannot find weekly cache file: {weekly_cache_file.name}. Aborting update.")
        return

    # Load the main raw data cache, or initialize if it doesn't exist
    raw_data = {}
    if raw_cache_file.exists():
        with open(raw_cache_file, "rb") as f:
            try:
                raw_data = pickle.load(f)
            except EOFError:
                logging.warning("raw_api_cache.pkl is empty or corrupted. Starting fresh.")

    # Load the new weekly data
    with open(weekly_cache_file, "rb") as f:
        weekly_matchups = pickle.load(f)

    # Ensure the season and weeks structure exists
    if season not in raw_data:
        raw_data[season] = {"weeks": {}}
    elif "weeks" not in raw_data[season]:
        raw_data[season]["weeks"] = {}

    # Add or overwrite the specific week's data
    raw_data[season]["weeks"][str(week)] = weekly_matchups

    # Save the updated data back to the main cache
    with open(raw_cache_file, "wb") as f:
        pickle.dump(raw_data, f)
    
    logging.info(f"✅ Successfully updated {raw_cache_file.name} with Week {week} data.")

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
    output_file = CACHE_DIR / "raw_api_cache.pkl"
    with open(output_file, "wb") as f:
        pickle.dump(complete_raw_data, f)
        
    logging.info(f"\n✅ Success! All raw API data saved to {output_file}")

if __name__ == "__main__":
    cache_all_raw_data()
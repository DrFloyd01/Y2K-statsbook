import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- CONFIGURATION ---
# The season you want to investigate
TARGET_SEASON = "2021"

# --- SCRIPT ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

try:
    with open("leagues.json", "r") as f:
        all_leagues = json.load(f)
except FileNotFoundError:
    logging.error("leagues.json not found!")
    exit()

config = all_leagues.get(TARGET_SEASON)
if not config:
    logging.error(f"Configuration for {TARGET_SEASON} not found in leagues.json")
    exit()

print(f"--- Checking Team Managers for {TARGET_SEASON} ---")

query = YahooFantasySportsQuery(
    league_id=config["league_id"], 
    game_code="nfl", 
    game_id=config["game_id"],
    yahoo_consumer_key=YAHOO_CONSUMER_KEY, 
    yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
    env_file_location=Path("."), 
    save_token_data_to_env_file=True
)

try:
    teams = query.get_league_teams()
    for team in teams:
        team_name = team.name.decode('utf-8')
        manager_nicknames = [mgr.nickname for mgr in team.managers]
        
        print(f"\nTeam: {team_name}")
        print(f"  Managers: {', '.join(manager_nicknames)}")

except Exception as e:
    logging.error(f"An error occurred: {e}")
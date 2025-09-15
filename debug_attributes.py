import json
import os
import logging
import pickle
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- CONFIGURATION ---
# A season where you know there was a playoff
TARGET_SEASON = "2018" 
# A known championship week for that season
PLAYOFF_WEEK = 15

# --- SCRIPT ---
load_dotenv()
YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

with open("leagues.json", "r") as f:
    config = json.load(f)[TARGET_SEASON]

query = YahooFantasySportsQuery(
    league_id=config["league_id"], game_code="nfl", game_id=config["game_id"],
    yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET
)

print(f"\n--- Fetching Scoreboard for {TARGET_SEASON}, Week {PLAYOFF_WEEK} ---")
scoreboard = query.get_league_scoreboard_by_week(PLAYOFF_WEEK)
matchup = scoreboard.matchups[0] # Just inspect the first matchup

print("\nAll available attributes for a playoff Matchup object:")
print("-" * 50)
# The vars() function gives us a dictionary of all attributes
for attribute, value in vars(matchup).items():
    print(f"{attribute}: {value}")
print("-" * 50)
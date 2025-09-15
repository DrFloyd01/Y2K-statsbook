import json

# --- CONFIGURATION ---
# IMPORTANT: Use the exact manager nicknames as they appear in your data files.
MANAGER_1 = "Mike"
MANAGER_2 = "Jasper"

# --- SCRIPT ---
print(f"Searching for all matchups between {MANAGER_1} and {MANAGER_2}...")
print("-" * 50)

found_games = 0

try:
    with open("historical_data.json", "r") as f:
        historical_data = json.load(f)
except FileNotFoundError:
    print("ERROR: historical_data.json not found. Please run build_history.py first.")
    exit()

for game in historical_data:
    # Create a set of the two managers in the current game
    managers_in_game = {game.get('team1_manager_name'), game.get('team2_manager_name')}
    
    # Check if this game is between the two managers we're looking for
    if managers_in_game == {MANAGER_1, MANAGER_2}:
        found_games += 1
        winner = game.get('winner_manager_name')
        print(f"Season: {game.get('season')}, Week: {game.get('week')}")
        
        # FIX: Use the new 'game_type' field instead of the old 'is_playoff'
        print(f"  - Game Type: {game.get('game_type', 'N/A')}")
        
        print(f"  - Score: {game.get('team1_manager_name')} ({game.get('team1_score')}) vs {game.get('team2_manager_name')} ({game.get('team2_score')})")
        print(f"  - Winner: {winner}\n")

if found_games == 0:
    print("No matchups found between these two managers in your history file.")
else:
    print(f"Found {found_games} total matchups.")
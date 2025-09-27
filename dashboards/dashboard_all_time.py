import json
from collections import defaultdict

# --- CONFIGURATION ---
# Merges the stats from the key's name into the value's name, then hides the key.
MANAGERS_TO_MERGE = {
    "--hidden--": "Ryan"
}
# Hides any manager from the final leaderboard.
MANAGERS_TO_HIDE = ["cooper", "nick", "Torin"]


def calculate_all_time_records():
    """
    Calculates and displays separate all-time records for regular season and playoffs.
    """
    try:
        with open("historical_data.json", "r") as f:
            historical_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: historical_data.json not found.")
        return

    # 1. Tally stats, keeping regular season and playoffs separate
    stats = defaultdict(lambda: {
        "reg_wins": 0, "reg_losses": 0, "reg_ties": 0,
        "playoff_wins": 0, "playoff_losses": 0, "playoff_ties": 0
    })

    for game in historical_data:
        game_type = game.get("game_type", "regular")
        if game_type == "consolation":
            continue

        m1 = game['team1_manager_name']
        m2 = game['team2_manager_name']
        winner = game['winner_manager_name']

        if game_type == 'regular':
            if winner:
                if winner == m1: stats[m1]['reg_wins'] += 1; stats[m2]['reg_losses'] += 1
                else: stats[m2]['reg_wins'] += 1; stats[m1]['reg_losses'] += 1
            else:
                stats[m1]['reg_ties'] += 1; stats[m2]['reg_ties'] += 1
        else: # Playoff game
            if winner:
                if winner == m1: stats[m1]['playoff_wins'] += 1; stats[m2]['playoff_losses'] += 1
                else: stats[m2]['playoff_wins'] += 1; stats[m1]['playoff_losses'] += 1
            else:
                stats[m1]['playoff_ties'] += 1; stats[m2]['playoff_ties'] += 1

    # 2. Merge manager records as defined in the config
    for source, target in MANAGERS_TO_MERGE.items():
        if source in stats:
            for key, value in stats[source].items():
                stats[target][key] += value
            del stats[source]

    # 3. Prepare and print both leaderboards
    print_leaderboard(stats, "Regular Season")
    print_leaderboard(stats, "Playoffs")


def print_leaderboard(stats, game_type):
    """
    Formats and prints a leaderboard for either Regular Season or Playoffs.
    """
    leaderboard = []
    
    prefix = "reg_" if game_type == "Regular Season" else "playoff_"
    
    for name, data in stats.items():
        if name in MANAGERS_TO_HIDE:
            continue
            
        wins = data[f'{prefix}wins']
        losses = data[f'{prefix}losses']
        ties = data[f'{prefix}ties']
        
        total_games = wins + losses + ties
        if total_games == 0: continue # Skip managers with no games of this type

        win_pct = wins / total_games
        leaderboard.append({
            "name": name, "wins": wins, "losses": losses, "ties": ties, "win_pct": win_pct
        })
        
    leaderboard.sort(key=lambda x: x['win_pct'], reverse=True)

    print(f"\n--- 🏈 Y2K All-Time {game_type} Leaderboard 🏈 ---")
    print("-" * 52)
    print(f"{'Rank':<5} {'Manager':<18} {'Record':<18} {'Win %':<7}")
    print("-" * 52)
    for i, entry in enumerate(leaderboard):
        rank = i + 1
        if entry['ties'] > 0:
            record_str = f"{entry['wins']}-{entry['losses']}-{entry['ties']}"
        else:
            record_str = f"{entry['wins']}-{entry['losses']}"
        win_pct_str = f"{entry['win_pct']:.3f}"
        print(f"{rank:<5} {entry['name']:<18} {record_str:<18} {win_pct_str:<7}")
    print("-" * 52)


if __name__ == "__main__":
    calculate_all_time_records()
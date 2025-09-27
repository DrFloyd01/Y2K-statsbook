import json

# --- CONFIGURATION ---
# Merges the stats from the key's name into the value's name.
MANAGERS_TO_MERGE = {
    "--hidden--": "Ryan"
}
# Hides any manager from the final leaderboard.
MANAGERS_TO_HIDE = ["cooper", "nick", "Torin"]

def load_h2h_data():
    """Loads the h2h_records.json file."""
    try:
        with open("h2h_records.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: h2h_records.json not found. Please run init_h2h_records.py first.")
        return None

def merge_manager_data(h2h_data):
    """
    Merges H2H records from a source manager to a target manager in-memory.
    This is a simplified merge for streak display; it doesn't re-calculate historical streaks.
    It prioritizes the target manager's existing record if a collision occurs.
    """
    for source, target in MANAGERS_TO_MERGE.items():
        keys_to_delete = []
        for key, record in h2h_data.items():
            if source in key:
                keys_to_delete.append(key)
                opponent = record['manager1_name'] if record['manager2_name'] == source else record['manager2_name']
                new_key = "-".join(sorted([target, opponent]))

                # If a record for the target already exists, we assume it's the primary one.
                # A more complex merge would require re-calculating streaks from raw game data.
                if new_key not in h2h_data:
                    # Remap the owner of the record before moving it
                    record['manager1_name'] = min(target, opponent)
                    record['manager2_name'] = max(target, opponent)
                    if record.get('longest_streak_holder') == source:
                        record['longest_streak_holder'] = target
                    h2h_data[new_key] = record

        for key in keys_to_delete:
            if key in h2h_data:
                del h2h_data[key]
    return h2h_data

def print_streak_leaderboard(h2h_data, top_n=15):
    """
    Calculates and prints a leaderboard of the longest all-time H2H streaks.
    """
    streaks = []
    hidden_lower = [h.lower() for h in MANAGERS_TO_HIDE]

    for record in h2h_data.values():
        if not record.get('longest_streak_holder') or not record.get('longest_streak_len'):
            continue

        winner = record['longest_streak_holder']
        loser = record['manager1_name'] if record['manager2_name'] == winner else record['manager2_name']

        if winner.lower() in hidden_lower or loser.lower() in hidden_lower:
            continue

        is_active = (record.get('longest_streak_holder') == record.get('streak_holder') and 
                     record.get('longest_streak_len') == record.get('streak_len'))

        start_game = record.get('longest_streak_start_game')
        end_game = record.get('longest_streak_end_game')
        date_range_str = "N/A"
        if start_game and end_game:
            start_str = f"Wk{start_game['week']}'{str(start_game['season'])[-2:]}"
            end_str = f"Wk{end_game['week']}'{str(end_game['season'])[-2:]}"
            date_range_str = f"{start_str} - {end_str}"

        streaks.append({
            'winner': winner, 'loser': loser, 'length': record['longest_streak_len'],
            'is_active': is_active, 'date_range': date_range_str
        })

    # Sort by streak length, descending
    sorted_streaks = sorted(streaks, key=lambda x: x['length'], reverse=True)

    print(f"\n--- 🔥 Top {top_n} All-Time H2H Winning Streaks 🔥 ---")
    header = f"{'Rank':<5} {'Streak':<8} {'Winner':<15} {'Loser':<15} {'Date Range':<22}"
    print(header)
    print("-" * len(header))
    for i, streak in enumerate(sorted_streaks[:top_n]):
        active_marker = "*" if streak['is_active'] else ""
        print(f"{i+1:<5} {str(streak['length']) + active_marker:<8} {streak['winner']:<15} {streak['loser']:<15} {streak['date_range']:<22}")
    print("-" * len(header))
    print("* = Active Streak")

def main():
    h2h_data = load_h2h_data()
    if h2h_data:
        merged_data = merge_manager_data(h2h_data)
        print_streak_leaderboard(merged_data)

if __name__ == "__main__":
    main()
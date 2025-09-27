import json
from collections import defaultdict

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
    """
    for source, target in MANAGERS_TO_MERGE.items():
        keys_to_delete = []
        for key, record in h2h_data.items():
            if source in key:
                keys_to_delete.append(key)
                
                # Find the opponent and the new key for the target manager
                opponent = record['manager1_name'] if record['manager2_name'] == source else record['manager2_name']
                new_key = "-".join(sorted([target, opponent]))

                # Ensure the target record exists, if not, create a shell
                if new_key not in h2h_data:
                    h2h_data[new_key] = {
                        "manager1_name": min(target, opponent), "manager2_name": max(target, opponent),
                        "reg_wins_1": 0, "reg_wins_2": 0, "playoff_wins_1": 0, "playoff_wins_2": 0,
                        "playoff_history": [], "streak_holder": None, "streak_len": 0, "last_game": {"season": 0, "week": 0}
                    }

                target_record = h2h_data[new_key]

                # Determine which manager is '1' and '2' in both records
                source_is_m1 = record['manager1_name'] == opponent
                target_is_m1 = target_record['manager1_name'] == opponent

                # Merge stats
                target_record['reg_wins_1' if target_is_m1 else 'reg_wins_2'] += record['reg_wins_1' if source_is_m1 else 'reg_wins_2']
                target_record['reg_wins_2' if target_is_m1 else 'reg_wins_1'] += record['reg_wins_2' if source_is_m1 else 'reg_wins_1']
                target_record['playoff_wins_1' if target_is_m1 else 'playoff_wins_2'] += record['playoff_wins_1' if source_is_m1 else 'playoff_wins_2']
                target_record['playoff_wins_2' if target_is_m1 else 'reg_wins_1'] += record['playoff_wins_2' if source_is_m1 else 'playoff_wins_1']

                # Merge playoff history and sort by season
                target_record['playoff_history'].extend(record['playoff_history'])
                target_record['playoff_history'].sort(key=lambda x: x['season'])

                # Update last game and streak (this is a simplification; a full re-calc would be needed for perfect streak logic)
                if record['last_game']['season'] > target_record['last_game']['season'] or \
                   (record['last_game']['season'] == target_record['last_game']['season'] and record['last_game']['week'] > target_record['last_game']['week']):
                    target_record['last_game'] = record['last_game']
                    # Note: Streak logic after merging is complex; this keeps the most recent game's streak.
                    target_record['streak_holder'] = record['streak_holder'].replace(source, target)
                    target_record['streak_len'] = record['streak_len']

        for key in keys_to_delete:
            del h2h_data[key]
    return h2h_data

def get_all_managers(h2h_data, hidden_managers):
    """Extracts all unique manager names from the H2H data."""
    managers = set()
    for record in h2h_data.values():
        managers.add(record['manager1_name'])
        managers.add(record['manager2_name'])
    return sorted([m for m in managers if m.lower() not in [h.lower() for h in hidden_managers]])

def calculate_and_print_leaderboards(h2h_data, hidden_managers):
    """
    Calculates and prints leaderboards for H2H dominance.
    """
    all_matchups = []
    hidden_lower = [h.lower() for h in hidden_managers]

    for key, record in h2h_data.items():
        m1, m2 = record['manager1_name'], record['manager2_name']
        if m1.lower() in hidden_lower or m2.lower() in hidden_lower:
            continue
        
        # Matchup from m1's perspective
        all_matchups.append({
            "manager": m1, "opponent": m2,
            "reg_wins": record['reg_wins_1'], "reg_losses": record['reg_wins_2'],
            "playoff_wins": record['playoff_wins_1'], "playoff_losses": record['playoff_wins_2']
        })
        # Matchup from m2's perspective
        all_matchups.append({
            "manager": m2, "opponent": m1,
            "reg_wins": record['reg_wins_2'], "reg_losses": record['reg_wins_1'],
            "playoff_wins": record['playoff_wins_2'], "playoff_losses": record['playoff_wins_1']
        })

    # --- Leaderboard Calculations ---
    # Regular Season
    reg_win_pct_board = sorted(
        [m for m in all_matchups if m['reg_wins'] >= 3 and (m['reg_wins'] + m['reg_losses']) > 0],
        key=lambda x: x['reg_wins'] / (x['reg_wins'] + x['reg_losses']),
        reverse=True
    )
    reg_total_wins_board = sorted(
        [m for m in all_matchups if m['reg_wins'] > 0],
        key=lambda x: x['reg_wins'],
        reverse=True
    )
    # Playoffs
    playoff_total_wins_board = sorted(
        [m for m in all_matchups if m['playoff_wins'] > 0],
        key=lambda x: x['playoff_wins'],
        reverse=True
    )

    # --- Printing ---
    print_leaderboard("Regular Season H2H Win % (min 3 wins)", reg_win_pct_board, "reg", top_n=10)
    print_leaderboard("Most Regular Season H2H Wins", reg_total_wins_board, "reg", top_n=10)
    # Not interesting: print_leaderboard("Playoff H2H Win % (min 2 wins)", playoff_win_pct_board, "playoff", top_n=10)
    print_leaderboard("Most Playoff H2H Wins", playoff_total_wins_board, "playoff", top_n=5)

def print_leaderboard(title, data, prefix, top_n=10):
    print(f"\n--- 🏆 Top {top_n} {title} 🏆 ---")
    header = f"{'Rank':<5} {'Manager':<15} {'Opponent':<15} {'Record':<10} {'Win %':<8}"
    print(header)
    print("-" * len(header))
    for i, m in enumerate(data[:top_n]):
        wins, losses = m[f'{prefix}_wins'], m[f'{prefix}_losses']
        win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
        print(f"{i+1:<5} {m['manager']:<15} {m['opponent']:<15} {f'{wins}-{losses}':<10} {f'{win_pct:.3f}':<8}")
    print("-" * len(header))

def main():
    h2h_data = load_h2h_data()
    if h2h_data:
        merged_h2h_data = merge_manager_data(h2h_data)
        calculate_and_print_leaderboards(merged_h2h_data, MANAGERS_TO_HIDE)

if __name__ == "__main__":
    main()
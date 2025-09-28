import json
import logging
import itertools

logging.basicConfig(level=logging.INFO, format='%(message)s')

def calculate_h2h_for_pair(name1, name2, all_matchups):
    relevant_games = [
        g for g in all_matchups 
        if {g['team1_manager_name'], g['team2_manager_name']} == {name1, name2}
    ]
    relevant_games.sort(key=lambda x: (x['season'], x['week']))
    
    if not relevant_games:
        return None

    n1_reg_wins, n2_reg_wins = 0, 0
    n1_playoff_wins, n2_playoff_wins = 0, 0
    playoff_history = []
    regular_history = []

    # <<< FIX IS HERE: Use game_type to correctly assign wins >>>
    for game in relevant_games:
        # Ignore consolation games completely
        if game['game_type'] == 'consolation':
            continue
        
        game_info = {"winner": game['winner_manager_name'], "type": game['game_type'], "season": game['season'], "week": game['week']}

        if game['winner_manager_name'] == name1:
            if game['game_type'] in ['QF', 'SF', '1st', '3rd']: 
                n1_playoff_wins += 1
                playoff_history.append(game_info)
            else:
                n1_reg_wins += 1
                regular_history.append(game_info)
        elif game['winner_manager_name'] == name2:
            if game['game_type'] in ['QF', 'SF', '1st', '3rd']: 
                n2_playoff_wins += 1
                playoff_history.append(game_info)
            else:
                n2_reg_wins += 1
                regular_history.append(game_info)

    # --- Streak Calculations ---
    # Longest streak calculation
    longest_streak_holder, longest_streak_len = None, 0
    longest_streak_start_game, longest_streak_end_game = None, None
    current_streak_start_game = None
    current_streak_holder, current_streak_len = None, 0
    for game in relevant_games:
        winner = game.get('winner_manager_name')
        if not winner: # Skip ties
            current_streak_holder, current_streak_len = None, 0
            continue
        
        if winner == current_streak_holder:
            current_streak_len += 1
        else:
            # New streak starts
            current_streak_holder = winner
            current_streak_len = 1
            current_streak_start_game = {"season": game['season'], "week": game['week']}
        
        if current_streak_len > longest_streak_len:
            longest_streak_len = current_streak_len
            longest_streak_holder = current_streak_holder
            longest_streak_start_game = current_streak_start_game
            longest_streak_end_game = {"season": game['season'], "week": game['week']}

    streak_holder_name, streak_len = None, 0
    last_game = relevant_games[-1]
    if last_game['winner_manager_name']:
        streak_holder_name = last_game['winner_manager_name']
        for game in reversed(relevant_games):
            if game['winner_manager_name'] == streak_holder_name:
                streak_len += 1
            else:
                break
    
    return {
        "manager1_name": name1,
        "manager2_name": name2,
        "reg_wins_1": n1_reg_wins,
        "reg_wins_2": n2_reg_wins,
        "playoff_wins_1": n1_playoff_wins,
        "playoff_wins_2": n2_playoff_wins,
        "playoff_history": playoff_history,
        "regular_history": regular_history,
        "streak_holder": streak_holder_name,
        "streak_len": streak_len,
        "longest_streak_holder": longest_streak_holder,
        "longest_streak_len": longest_streak_len,
        "longest_streak_start_game": longest_streak_start_game,
        "longest_streak_end_game": longest_streak_end_game,
        "last_game": {"season": last_game['season'], "week": last_game['week']}
    }

def initialize_h2h_records():
    """
    Builds the entire h2h_records.json from historical_data.json.
    This is the definitive source for H2H data.
    """
    logging.info("Building H2H records from historical_data.json...")
    try:
        with open("data/historical_data.json", "r") as f:
            historical_data = json.load(f)
    except FileNotFoundError:
        logging.error("ERROR: historical_data.json not found. Please run init_history.py first.")
        return

    # Identify all unique managers by nickname
    manager_names = set()
    for game in historical_data:
        manager_names.add(game['team1_manager_name'])
        manager_names.add(game['team2_manager_name'])
    
    logging.info(f"Found {len(manager_names)} unique managers in league history.")

    # Generate all unique pairs of managers
    manager_pairs = list(itertools.combinations(manager_names, 2))
    
    logging.info(f"Calculating H2H records for {len(manager_pairs)} unique pairs...")

    # Calculate H2H for each pair and store it
    all_h2h_records = {}
    for name1, name2 in manager_pairs:
        h2h_record = calculate_h2h_for_pair(name1, name2, historical_data)
        
        if h2h_record:
            key = "-".join(sorted([name1, name2]))
            all_h2h_records[key] = h2h_record

    # Save the final dictionary to a new file
    with open("data/h2h_records.json", "w") as f:
        json.dump(all_h2h_records, f, indent=2)
        
    logging.info("\n✅ Success! h2h_records.json has been created based on manager nicknames.")

if __name__ == "__main__":
    initialize_h2h_records()
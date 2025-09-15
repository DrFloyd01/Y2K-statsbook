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

    # <<< FIX IS HERE: Use game_type to correctly assign wins >>>
    for game in relevant_games:
        # Ignore consolation games completely
        if game['game_type'] == 'consolation':
            continue

        if game['winner_manager_name'] == name1:
            if game['game_type'] in ['QF', 'SF', '1st', '3rd']: 
                n1_playoff_wins += 1
                playoff_history.append({"winner": name1, "type": game['game_type'], "season": game['season']})
            else:
                n1_reg_wins += 1
        elif game['winner_manager_name'] == name2:
            if game['game_type'] in ['QF', 'SF', '1st', '3rd']: 
                n2_playoff_wins += 1
                playoff_history.append({"winner": name2, "type": game['game_type'], "season": game['season']})
            else:
                n2_reg_wins += 1

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
        "playoff_history": playoff_history, # <-- Add the new list to the record
        "streak_holder": streak_holder_name,
        "streak_len": streak_len,
        "last_game": {"season": last_game['season'], "week": last_game['week']}
    }

def main():
    logging.info("Loading historical data...")
    try:
        with open("historical_data.json", "r") as f:
            historical_data = json.load(f)
    except FileNotFoundError:
        logging.error("ERROR: historical_data.json not found. Please run the updated build_history.py first.")
        return

    # 1. Identify all unique managers by nickname
    manager_names = set()
    for game in historical_data:
        manager_names.add(game['team1_manager_name'])
        manager_names.add(game['team2_manager_name'])
    
    logging.info(f"Found {len(manager_names)} unique managers in league history.")

    # 2. Generate all unique pairs of managers
    manager_pairs = list(itertools.combinations(manager_names, 2))
    
    logging.info(f"Calculating H2H records for {len(manager_pairs)} unique pairs...")

    # 3. Calculate H2H for each pair and store it
    all_h2h_records = {}
    for name1, name2 in manager_pairs:
        h2h_record = calculate_h2h_for_pair(name1, name2, historical_data)
        
        if h2h_record:
            key = "-".join(sorted([name1, name2]))
            all_h2h_records[key] = h2h_record

    # 4. Save the final dictionary to a new file
    with open("h2h_records.json", "w") as f:
        json.dump(all_h2h_records, f, indent=2)
        
    logging.info("\n✅ Success! h2h_records.json has been created based on manager nicknames.")

if __name__ == "__main__":
    main()
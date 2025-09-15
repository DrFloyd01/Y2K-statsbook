import json
from collections import defaultdict

# --- CONFIGURATION ---
# Merges the stats from the key's name into the value's name.
MANAGERS_TO_MERGE = {
    "--hidden--": "Ryan"
}
# Hides any manager from the final leaderboard.
MANAGERS_TO_HIDE = ["cooper", "nick", "Torin", "--hidden--"]
# Hides the current season from calculations.
SEASONS_TO_HIDE = [2025]

def get_ordinal(n):
    """Converts a number to its ordinal form (e.g., 1 -> 1st, 2 -> 2nd)."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

def calculate_regular_season_stats(season, historical_data):
    """
    Calculates regular season standings and Points For for a given season.
    Returns a tuple: (ranked_manager_map, manager_records_dict)
    """
    # ... (This helper function remains the same as before) ...
    season_games = [g for g in historical_data if g['season'] == season and g['game_type'] == 'regular']
    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'pf': 0.0})
    managers = set()
    for g in season_games:
        m1, m2, s1, s2, winner = g['team1_manager_name'], g['team2_manager_name'], g['team1_score'], g['team2_score'], g['winner_manager_name']
        managers.add(m1); managers.add(m2)
        records[m1]['pf'] += s1; records[m2]['pf'] += s2
        if winner:
            if winner == m1: records[m1]['wins'] += 1; records[m2]['losses'] += 1
            else: records[m2]['wins'] += 1; records[m1]['losses'] += 1
        else:
            records[m1]['ties'] += 1; records[m2]['ties'] += 1
    sorted_managers = sorted(managers, key=lambda m: (records[m]['wins'], records[m]['pf']), reverse=True)
    rank_map = {manager: i + 1 for i, manager in enumerate(sorted_managers)}
    return rank_map, records

def print_finishes_grid(manager_final_ranks, all_seasons, scoring_champs, season_team_counts):
    """
    Prints a grid view of finishes, with emojis and corrected alignment.
    """
    print("\n--- 🏁 Y2K Season-by-Season Finishes Grid 🏁 ---")
    
    header = f"{'Manager':<18}" + "".join([f"{str(s):<8}" for s in all_seasons])
    print(header)
    print("-" * len(header))

    sorted_managers = sorted(manager_final_ranks.items(), key=lambda item: item[0])
    
    for name, finishes in sorted_managers:
        if name.lower() in [n.lower() for n in MANAGERS_TO_HIDE]:
            continue
            
        finish_map = {f['season']: f['rank'] for f in finishes}
        row = f"{name:<18}"
        
        for season in all_seasons:
            rank = finish_map.get(season, '-')
            last_place_rank = season_team_counts.get(season)
            
            display_text = str(rank)
            if rank == 1:
                display_text = "🏆"
            elif rank == last_place_rank:
                display_text = "🗿"
            
            if scoring_champs.get(season) == name:
                display_text += "!"
            
            # <<< FIX: Adjust padding for wider emoji characters >>>
            has_emoji = "🏆" in display_text or "🗿" in display_text
            padding = 7 if has_emoji else 8
            
            row += f"{display_text:<{padding}}"
        
        print(row)
    
    print("-" * len(header))
    # <<< FIX: Update the key with all symbols >>>
    print("Key: 🏆 = 1st Place  |  🗿 = Last Place  |  ! = Scoring Champ")
    print("-" * len(header))
def calculate_all_time_final_standings():
    """
    Calculates final season rank for each manager for each year,
    then aggregates the results into an all-time leaderboard.
    """
    try:
        with open("historical_data.json", "r") as f:
            historical_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: historical_data.json not found.")
        return

    all_seasons = sorted(list(set(g['season'] for g in historical_data)))
    manager_final_ranks = defaultdict(list)
    scoring_champs_by_season = {} # <-- New dict to store scoring champs
    season_team_counts = {} # <-- New dict to store team counts per season
    
    # --- Phase 1: Calculate Final Rank for each Manager, for each Season ---
    for season in all_seasons:
        # Skips seasons as defined in the config
        if season in SEASONS_TO_HIDE:
            continue
        # ... (This entire section for calculating ranks is the same as before) ...
        reg_season_rank_map, reg_season_records = calculate_regular_season_stats(season, historical_data)
        
        # <<< FIX IS HERE: Store the number of teams for this season >>>
        season_team_counts[season] = len(reg_season_rank_map)

        # <<< NEW: Find and store the scoring champ for the season >>>
        if reg_season_records:
            scoring_champ = max(reg_season_records, key=lambda m: reg_season_records[m]['pf'])
            scoring_champs_by_season[season] = scoring_champ
        
        season_games = [g for g in historical_data if g['season'] == season]
        final_ranks_this_season = {}
        qf_losers = []
        playoff_games = [g for g in season_games if g['game_type'] in ['QF', 'SF', '1st', '3rd']]
        for g in playoff_games:
            m1, m2 = g['team1_manager_name'], g['team2_manager_name']
            winner, loser = (m1, m2) if g['winner_manager_name'] == m1 else (m2, m1)
            if g['game_type'] == '1st': final_ranks_this_season[winner] = 1; final_ranks_this_season[loser] = 2
            elif g['game_type'] == '3rd': final_ranks_this_season[winner] = 3; final_ranks_this_season[loser] = 4
            elif g['game_type'] == 'QF': qf_losers.append(loser)
        if qf_losers:
            qf_loser1_reg_rank = reg_season_rank_map.get(qf_losers[0], 99)
            qf_loser2_reg_rank = reg_season_rank_map.get(qf_losers[1], 99)
            if qf_loser1_reg_rank < qf_loser2_reg_rank: final_ranks_this_season[qf_losers[0]] = 5; final_ranks_this_season[qf_losers[1]] = 6
            else: final_ranks_this_season[qf_losers[1]] = 5; final_ranks_this_season[qf_losers[0]] = 6
        for manager_name, reg_rank in reg_season_rank_map.items():
            try: final_rank = final_ranks_this_season.get(manager_name, reg_rank)
            except: final_rank = reg_rank
            # Store as a dictionary to keep season and rank together
            manager_final_ranks[manager_name].append({"season": season, "rank": final_rank})
    
    # --- Phase 2: Merge and Aggregate Data ---

    # <<< FIX IS HERE: Merge manager records as defined in the config >>>
    for source, target in MANAGERS_TO_MERGE.items():
        if source in manager_final_ranks:
            manager_final_ranks[target].extend(manager_final_ranks[source])
            del manager_final_ranks[source]

    leaderboard = []
    for name, finishes in manager_final_ranks.items():
        # <<< FIX IS HERE: Hide managers as defined in the config >>>
        if name.lower() in [n.lower() for n in MANAGERS_TO_HIDE]:
            continue
        ranks = [f['rank'] for f in finishes]
        avg_finish = sum(ranks) / len(ranks)
        finish_counts = defaultdict(int)
        for r in ranks: finish_counts[r] += 1
        leaderboard.append({
            "name": name, "avg_finish": avg_finish,
            "seasons": len(ranks), "finishes": dict(finish_counts)
        })
    leaderboard.sort(key=lambda x: x['avg_finish'])

    # --- Phase 3: Display the Leaderboard ---
    print("\n--- 🏆 Y2K All-Time Final Standings 🏆 ---")
    print("(Sorted by Average Finish)")
    header = f"{'Rank':<5} {'Manager':<18} {'Avg Finish':<12} {'Seasons':<10}"
    pos_headers = " ".join([f"{i:<3}" for i in range(1, 13)])
    print(header + pos_headers)
    print("-" * (len(header) + len(pos_headers)))
    for i, data in enumerate(leaderboard):
        rank = i + 1
        avg_finish_str = f"{data['avg_finish']:.2f}"
        main_stats = f"{rank:<5} {data['name']:<18} {avg_finish_str:<12} {data['seasons']:<10}"
        finish_strs = [f"{data['finishes'].get(pos, 0):<3}" for pos in range(1, 13)]
        print(main_stats + " ".join(finish_strs))
    print("-" * (len(header) + len(pos_headers)))

    # --- NEW: Print Chronological Finishes ---
    print("\n--- ⌛ Y2K Manager Finishing History ⌛ ---")
    
    # Sort managers alphabetically for this view
    sorted_managers = sorted(manager_final_ranks.items(), key=lambda item: item[0])
    
    for name, finishes in sorted_managers:
        if name.lower() in [n.lower() for n in MANAGERS_TO_HIDE]:
            continue
        
        # Sort this manager's finishes by season
        finishes.sort(key=lambda x: x['season'])
        
        # Create the formatted string: "1st (2018), 3rd (2019), ..."
        history_parts = [f"{get_ordinal(f['rank'])} ({f['season']})" for f in finishes]
        history_str = ", ".join(history_parts)
        
        print(f"\n{name}:")
        print(f"  {history_str}")
    print("\n" + "-"*45)

    # <<< NEW: Call the new grid printing function at the end >>>
    print_finishes_grid(manager_final_ranks, all_seasons, scoring_champs_by_season, season_team_counts)

if __name__ == "__main__":
    calculate_all_time_final_standings()
import json
import statistics
from collections import defaultdict

# --- CONFIGURATION ---
MANAGERS_TO_MERGE = {
    "--hidden--": "Ryan"
}
MANAGERS_TO_HIDE = ["cooper", "nick", "Torin", "--hidden--"]
# Hides the current season from calculations.
SEASONS_TO_HIDE = [2025]

def load_historical_data():
    """Loads the historical_data.json file."""
    try:
        with open("historical_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: historical_data.json not found. Please run build_history.py first.")
        return None

def process_data(historical_data):
    """
    Processes historical data to calculate accolades and alternative standings.
    """
    # Group games by season and week
    games_by_week = defaultdict(list)
    for game in [g for g in historical_data if g['season'] not in SEASONS_TO_HIDE]:
        if game.get("game_type") == "regular":
            games_by_week[f"{game['season']}-{game['week']}"].append(game)

    # This will store the raw data for each accolade, per season
    seasonal_accolades = defaultdict(lambda: defaultdict(lambda: []))
    
    for week_key, games in games_by_week.items():
        season, week = week_key.split('-')
        season = int(season)
        
        weekly_scores = []
        for game in games:
            m1, m2 = game['team1_manager_name'], game['team2_manager_name']
            s1, s2 = game['team1_score'], game['team2_score']
            weekly_scores.append({'manager': m1, 'score': s1, 'winner': game['winner_manager_name'], 'opponent': m2})
            weekly_scores.append({'manager': m2, 'score': s2, 'winner': game['winner_manager_name'], 'opponent': m1})
        
        weekly_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # --- Accolade & Alt Universe Calculations for the week ---
        num_teams = len(weekly_scores)
        median_index = num_teams // 2

        # Track total games for Alt Universe W-L
        for team in weekly_scores:
            seasonal_accolades[season]['total_games'].append(team['manager'])

        # Alternative Universe Wins
        for team in weekly_scores[:median_index]:
            seasonal_accolades[season]['alt_universe_wins'].append(team['manager'])

        # Top Points
        top_team = weekly_scores[0]
        seasonal_accolades[season]['top_points'].append({
            'manager': top_team['manager'], 'score': top_team['score'], 
            'opponent': top_team['opponent'], 'season': season, 'week': int(week)
        })

        # Highest Scoring Loss
        losing_teams = [t for t in weekly_scores if t['winner'] and t['manager'] != t['winner']]
        if losing_teams:
            highest_scoring_loser = max(losing_teams, key=lambda x: x['score'])
            seasonal_accolades[season]['highest_scoring_loss'].append({
                'manager': highest_scoring_loser['manager'], 'score': highest_scoring_loser['score'],
                'opponent': highest_scoring_loser['opponent'], 'season': season, 'week': int(week)
            })

        # Lowest Scoring Win
        winning_teams = [t for t in weekly_scores if t['winner'] and t['manager'] == t['winner']]
        if winning_teams:
            lowest_scoring_winner = min(winning_teams, key=lambda x: x['score'])
            seasonal_accolades[season]['lowest_scoring_win'].append({
                'manager': lowest_scoring_winner['manager'], 'score': lowest_scoring_winner['score'],
                'opponent': lowest_scoring_winner['opponent'], 'season': season, 'week': int(week)
            })

        # Smallest Margin of Defeat
        min_margin, smd_details = float('inf'), None
        for game in games:
            if game['winner_manager_name']: # Not a tie
                margin = abs(game['team1_score'] - game['team2_score'])
                if margin < min_margin:
                    min_margin = margin
                    loser = game['team1_manager_name'] if game['winner_manager_name'] == game['team2_manager_name'] else game['team2_manager_name']
                    winner = game['winner_manager_name']
                    smd_details = {
                        'manager': loser, 'margin': margin, 'opponent': winner,
                        'season': season, 'week': int(week)
                    }
        if smd_details:
            seasonal_accolades[season]['smallest_margin_defeat'].append(smd_details)

        # Blowout of the Week
        max_margin, blowout_details = 0, None
        for game in games:
            if game['winner_manager_name']:
                margin = abs(game['team1_score'] - game['team2_score'])
                if margin > max_margin:
                    max_margin = margin
                    winner = game['winner_manager_name']
                    loser = game['team1_manager_name'] if winner == game['team2_manager_name'] else game['team2_manager_name']
                    blowout_details = {
                        'manager': winner, 'margin': margin, 'opponent': loser,
                        'season': season, 'week': int(week)
                    }
        if blowout_details:
            seasonal_accolades[season]['blowout_win'].append(blowout_details)

        # Rollercoaster Award (collect scores)
        for team in weekly_scores:
            seasonal_accolades[season]['scores'].append({'manager': team['manager'], 'score': team['score']})

    return seasonal_accolades

def merge_and_tally_stats(seasonal_accolades):
    """
    Merges manager data and tallies the accolades for final display.
    """
    all_time_stats = defaultdict(lambda: defaultdict(int))
    per_season_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    # This will store the most extreme instance of each accolade for each season
    per_season_records = defaultdict(lambda: {
        'top_points': {'score': 0},
        'highest_scoring_loss': {'score': 0},
        'lowest_scoring_win': {'score': float('inf')},
        'smallest_margin_defeat': {'margin': float('inf')},
        'blowout_win': {'margin': 0}
    })
    # This will store the most extreme instance of each accolade
    all_time_records = {
        'top_points': {'score': 0}, 'highest_scoring_loss': {'score': 0},
        'lowest_scoring_win': {'score': float('inf')}, 'smallest_margin_defeat': {'margin': float('inf')},
        'blowout_win': {'margin': 0}
    }

    for season, accolades in seasonal_accolades.items():
        for accolade_type, items in accolades.items():
            if accolade_type == 'scores': continue # Handle scores separately for stdev
            for item in items:
                final_manager = MANAGERS_TO_MERGE.get(item if isinstance(item, str) else item['manager'], item if isinstance(item, str) else item['manager'])
                per_season_stats[season][final_manager][accolade_type] += 1
                all_time_stats[final_manager][accolade_type] += 1
    
    # Calculate Rollercoaster Award (stdev)
    for season, accolades in seasonal_accolades.items():
        scores_by_manager = defaultdict(list)
        for score_data in accolades['scores']:
            final_manager = MANAGERS_TO_MERGE.get(score_data['manager'], score_data['manager'])
            scores_by_manager[final_manager].append(score_data['score'])
        
        for manager, scores in scores_by_manager.items():
            if len(scores) > 1:
                stdev = statistics.stdev(scores)
                per_season_stats[season][manager]['rollercoaster_stdev'] = stdev

    # Calculate All-Time Stdev
    all_time_scores_by_manager = defaultdict(list)
    for season, accolades in seasonal_accolades.items():
        for score_data in accolades['scores']:
            final_manager = MANAGERS_TO_MERGE.get(score_data['manager'], score_data['manager'])
            all_time_scores_by_manager[final_manager].append(score_data['score'])
    
    for manager, scores in all_time_scores_by_manager.items():
        if len(scores) > 1:
            stdev = statistics.stdev(scores)
            all_time_stats[manager]['all_time_stdev'] = stdev


    # Find all-time and per-season record holders for single events
    for season, accolades in seasonal_accolades.items():
        for key in all_time_records.keys():
            if key in accolades:
                # Per-Season
                if key == 'top_points' or key == 'highest_scoring_loss':
                    seasonal_best = max(accolades[key], key=lambda x: x['score'])
                    if seasonal_best['score'] > per_season_records[season][key]['score']:
                        per_season_records[season][key] = seasonal_best
                    if seasonal_best['score'] > all_time_records[key]['score']:
                        all_time_records[key] = seasonal_best
                elif key == 'lowest_scoring_win':
                    seasonal_worst = min(accolades[key], key=lambda x: x['score'])
                    if seasonal_worst['score'] < per_season_records[season][key]['score']:
                        per_season_records[season][key] = seasonal_worst
                    if seasonal_worst['score'] < all_time_records[key]['score']:
                        all_time_records[key] = seasonal_worst
                elif key == 'smallest_margin_defeat' or key == 'blowout_win':
                    comparator = min if key == 'smallest_margin_defeat' else max
                    seasonal_extreme = comparator(accolades[key], key=lambda x: x['margin'])
                    
                    # Per-Season
                    current_seasonal_extreme_margin = per_season_records[season][key]['margin']
                    if (comparator(seasonal_extreme['margin'], current_seasonal_extreme_margin) == seasonal_extreme['margin']):
                         per_season_records[season][key] = seasonal_extreme

                    # All-Time
                    current_all_time_extreme_margin = all_time_records[key]['margin']
                    if (comparator(seasonal_extreme['margin'], current_all_time_extreme_margin) == seasonal_extreme['margin']):
                        all_time_records[key] = seasonal_extreme

    return all_time_stats, per_season_stats, all_time_records, per_season_records

def _format_record_string(record):
    """Helper to format the record detail string."""
    manager = MANAGERS_TO_MERGE.get(record.get('manager'), record.get('manager'))
    opponent = MANAGERS_TO_MERGE.get(record.get('opponent'), record.get('opponent'))
    season_str = str(record.get('season', ''))[-2:]
    week_str = record.get('week', '')

    if 'score' in record:
        # For score-based accolades, show opponent
        return f"{record['score']:.2f} pts (by {manager} vs {opponent}, Wk {week_str}'{season_str})"
    elif 'margin' in record:
        # For margin-based accolades
        return f"{record['margin']:.2f} pts (by {manager} vs {opponent}, Wk {week_str}'{season_str})"
    return "N/A"

def calculate_final_ranks(historical_data, seasons_to_process):
    """
    Calculates the final rank for each manager for each season.
    """
    final_ranks_by_season = defaultdict(dict)
    for season in seasons_to_process:
        # Regular season standings
        season_games_reg = [g for g in historical_data if g['season'] == season and g['game_type'] == 'regular']
        records = defaultdict(lambda: {'wins': 0, 'pf': 0.0})
        managers = set()
        for g in season_games_reg:
            m1, m2 = g['team1_manager_name'], g['team2_manager_name']
            managers.add(m1); managers.add(m2)
            records[m1]['pf'] += g['team1_score']; records[m2]['pf'] += g['team2_score']
            if g['winner_manager_name'] == m1: records[m1]['wins'] += 1
            elif g['winner_manager_name'] == m2: records[m2]['wins'] += 1
        
        sorted_managers = sorted(list(managers), key=lambda m: (records[m]['wins'], records[m]['pf']), reverse=True)
        reg_season_rank_map = {manager: i + 1 for i, manager in enumerate(sorted_managers)}

        # Final standings including playoffs
        playoff_games = [g for g in historical_data if g['season'] == season and g['game_type'] in ['QF', 'SF', '1st', '3rd']]
        final_ranks_this_season = {}
        for g in playoff_games:
            winner, loser = (g['team1_manager_name'], g['team2_manager_name']) if g['winner_manager_name'] == g['team1_manager_name'] else (g['team2_manager_name'], g['team1_manager_name'])
            if g['game_type'] == '1st': final_ranks_this_season[winner] = 1; final_ranks_this_season[loser] = 2
            elif g['game_type'] == '3rd': final_ranks_this_season[winner] = 3; final_ranks_this_season[loser] = 4

        for manager_name, reg_rank in reg_season_rank_map.items():
            final_rank = final_ranks_this_season.get(manager_name, reg_rank)
            final_ranks_by_season[season][manager_name] = final_rank
            
    return final_ranks_by_season

def print_leaderboards(all_time_stats, per_season_stats, all_time_records, per_season_records, final_ranks_by_season):
    """
    Prints all the calculated leaderboards in a readable format.
    """
    hidden_lower = [h.lower() for h in MANAGERS_TO_HIDE]

    def get_filtered_managers(stats_dict):
        return [m for m in stats_dict if m.lower() not in hidden_lower]

    # --- All-Time Leaderboards ---
    print("\n" + "="*75)
    print("👑 Y2K All-Time Regular Season Leaderboards 👑".center(75))
    print("="*75)
    
    all_time_managers = get_filtered_managers(all_time_stats)
    manager_seasons_played = {m: len([s for s, data in per_season_stats.items() if m in data]) for m in all_time_managers}

    # Alt Universe
    alt_universe_board = sorted(all_time_managers, key=lambda m: all_time_stats[m]['alt_universe_wins'] / manager_seasons_played.get(m, 1) if manager_seasons_played.get(m, 1) > 0 else 0, reverse=True)
    print("\n--- 🌌 All-Time Alternative Universe Standings ---")
    header = f"{'Rank':<5} {'Manager':<18} {'Record (W-L)':<15} {'Wins/Season':<15} {'St. Dev.':<10}"
    print(header)
    print("-" * len(header))
    for i, m in enumerate(alt_universe_board):
        wins = all_time_stats[m]['alt_universe_wins']
        total_games = all_time_stats[m]['total_games']
        losses = total_games - wins
        seasons = manager_seasons_played.get(m, 1)
        wins_per_season = wins / seasons if seasons > 0 else 0
        stdev = all_time_stats[m].get('all_time_stdev', 0)
        record_str = f"{wins}-{losses}"
        print(f"{i+1:<5} {m:<18} {record_str:<15} {f'{wins_per_season:.2f}':<15} {f'{stdev:.2f}':<10}")

    # All-Time Trophy Case
    accolade_map = {
        'top_points': ("🌋 Top Point Weeks", "Top Score"),
        'highest_scoring_loss': ("💔 Tough Luck Losses", "Highest Scoring Loss"),
        'lowest_scoring_win': ("🍀 Luckiest Wins", "Lowest Scoring Win"),
        'smallest_margin_defeat': ("🤏 Heartbreak Losses", "Closest Margin of Defeat"),
        'blowout_win': ("💥 Biggest Blowouts", "Largest Margin of Victory")
    }

    print("\n--- 🏆 All-Time Trophy Case 🏆 ---")
    for key, (count_title, record_title) in accolade_map.items():
        board = sorted(all_time_managers, key=lambda m: all_time_stats[m][key], reverse=True)
        if not board or all_time_stats[board[0]][key] == 0: continue
        
        holder = board[0]
        count = all_time_stats[holder][key]
        record = all_time_records.get(key)

        print(f"\n{count_title}")
        print(f"  - Most: {holder} ({count} times)")
        if record and 'manager' in record:
            print(f"  - Record: {_format_record_string(record)}")

    # --- Per-Season Leaderboards ---
    for season in sorted(per_season_stats.keys()):
        print("\n" + "="*75)
        print(f"👑 {season} Season Accolade Leaderboard 👑".center(75))
        print("="*75)

        season_managers = list(per_season_stats[season].keys())
        season_ranks = final_ranks_by_season.get(season, {})

        # Alt Universe
        # Sort by actual final rank for the season
        alt_universe_board = sorted(season_managers, key=lambda m: season_ranks.get(MANAGERS_TO_MERGE.get(m, m), 999))
        print("\n--- 🌌 Alternative Universe Standings (W-L) ---")
        header = f"{'Fin.':<5} {'Manager':<18} {'Record':<12} {'St. Dev.':<10}"; print(header); print("-" * len(header))
        for i, m in enumerate(alt_universe_board):
            wins = per_season_stats[season][m]['alt_universe_wins']
            losses = per_season_stats[season][m]['total_games'] - wins
            stdev = per_season_stats[season][m].get('rollercoaster_stdev', 0.0)
            actual_finish = season_ranks.get(MANAGERS_TO_MERGE.get(m, m), "-")
            print(f"{actual_finish:<5} {m:<18} {f'{wins}-{losses}':<12} {f'{stdev:.2f}':<10}")

        # Per-Season Trophy Case
        print("\n--- 🏆 Season Trophy Case 🏆 ---")
        for key, (count_title, record_title) in accolade_map.items():
            board = sorted(season_managers, key=lambda m: per_season_stats[season][m][key], reverse=True)
            if not board or per_season_stats[season][board[0]][key] == 0: continue

            # Find winner(s) for most occurrences
            max_count = per_season_stats[season][board[0]][key]
            ties = [m for m in board if per_season_stats[season][m][key] == max_count]
            winner_str = " & ".join(ties)

            record = per_season_records[season].get(key)

            print(f"\n{count_title}")
            print(f"  - Winner(s): {winner_str} ({max_count}x)")
            if record and 'manager' in record:
                print(f"  - {record_title}: {_format_record_string(record)}")

def main():
    historical_data = load_historical_data()
    if not historical_data:
        return

    print("Processing historical data for accolades...")
    seasonal_accolades = process_data(historical_data)
    
    print("Tallying stats and merging manager data...")
    all_time_stats, per_season_stats, all_time_records, per_season_records = merge_and_tally_stats(seasonal_accolades)
    
    final_ranks = calculate_final_ranks(historical_data, per_season_stats.keys())
    print_leaderboards(all_time_stats, per_season_stats, all_time_records, per_season_records, final_ranks)

if __name__ == "__main__":
    main()
import json
import logging
import pickle
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(message)s')

# --- Directory Setup ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = Path("cache")


def build_historical_data_from_cache():
    """
    Builds historical_data.json by processing the local raw_api_cache.pkl file.
    Includes logic for co-managers and correct playoff round identification.
    """
    # --- CONFIGURATION ---
    YOUR_NICKNAME = "Dylan"  # The script will use this for the co-manager rule

    def get_primary_manager(team, operator_nickname):
        """
        Selects the primary manager, prioritizing non-operators in co-manager situations.
        """
        if len(team.managers) == 1:
            return team.managers[0]
        else: # Co-manager situation
            other_managers = [m for m in team.managers if m.nickname != operator_nickname]
            if len(other_managers) > 0:
                return other_managers[0] # Assume the other manager is primary
            else:
                return team.managers[0] # Failsafe

    # --- (Loading local data is the same) ---
    cache_file = CACHE_DIR / "raw_api_cache.pkl"
    logging.info(f"Loading raw data from cache ({cache_file})...")
    try:
        with open(cache_file, "rb") as f:
            raw_data = pickle.load(f)
    except FileNotFoundError:
        logging.error(f"ERROR: {cache_file} not found. Please run build_raw_data_cache.py first.")
        return

    all_matchups_data = []

    for season, season_data in raw_data.items():
        logging.info(f"--- Processing Season: {season} ---")
        
        settings = season_data.get("settings")
        weeks_data = season_data.get("weeks")
        if not settings or not weeks_data: continue

        playoff_start_week = int(settings.playoff_start_week)
        num_playoff_teams = int(settings.num_playoff_teams)
        
        # --- PASS 1: Manually calculate regular season standings to find bye teams ---
        reg_season_records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pf': 0.0})
        managers = set()
        for week_str, matchups in weeks_data.items():
            if int(week_str) >= playoff_start_week: continue
            for m in matchups:
                team1, team2 = m.teams[0], m.teams[1]
                manager1 = get_primary_manager(team1, YOUR_NICKNAME)
                manager2 = get_primary_manager(team2, YOUR_NICKNAME)
                managers.add(manager1.nickname); managers.add(manager2.nickname)
                reg_season_records[manager1.nickname]['pf'] += team1.points
                reg_season_records[manager2.nickname]['pf'] += team2.points
                winner_check = manager1.nickname if team1.points > team2.points else manager2.nickname
                if winner_check == manager1.nickname: reg_season_records[manager1.nickname]['wins'] += 1; reg_season_records[manager2.nickname]['losses'] += 1
                else: reg_season_records[manager2.nickname]['wins'] += 1; reg_season_records[manager1.nickname]['losses'] += 1
        sorted_managers = sorted(list(managers), key=lambda m: (reg_season_records[m]['wins'], reg_season_records[m]['pf']), reverse=True)
        top_seeds_with_byes = sorted_managers[:2] if num_playoff_teams >= 6 else []
        
        # --- PASS 2: Process all games and assign correct game_type ---
        qf_winners, semi_final_winners, semi_final_losers = [], [], []

        for week_str, matchups in weeks_data.items():
            week = int(week_str)
            logging.info(f"Processing cached data for {season}, Week {week}...")

            for m in matchups:
                team1, team2 = m.teams[0], m.teams[1]
                manager1 = get_primary_manager(team1, YOUR_NICKNAME)
                manager2 = get_primary_manager(team2, YOUR_NICKNAME)

                # <<< FIX IS HERE: Define both winner and loser at the same time >>>
                winner, loser = (None, None)
                if not m.is_tied:
                    winner_by_score = manager1.nickname if team1.points > team2.points else manager2.nickname
                    if winner_by_score == manager1.nickname:
                        winner, loser = manager1.nickname, manager2.nickname
                    else:
                        winner, loser = manager2.nickname, manager1.nickname
                
                # <<< FIX IS HERE: Restructured logic to prioritize consolation check >>>
                game_type = "regular"
                if m.is_consolation:
                    game_type = "consolation"
                elif m.is_playoffs:
                    week_offset = week - playoff_start_week
                    if num_playoff_teams >= 6:
                        if week_offset == 0:
                            game_type = "QF"; qf_winners.append(winner)
                        elif week_offset == 1:
                            possible_sf_teams = set(qf_winners + top_seeds_with_byes)
                            if {manager1.nickname, manager2.nickname}.issubset(possible_sf_teams):
                                game_type = "SF"; semi_final_winners.append(winner); semi_final_losers.append(loser)
                            else: game_type = "consolation"
                        elif week_offset == 2:
                            if {manager1.nickname, manager2.nickname}.issubset(semi_final_winners): game_type = "1st"
                            elif {manager1.nickname, manager2.nickname}.issubset(semi_final_losers): game_type = "3rd"
                            else: game_type = "consolation"
                    else: # 4-team playoff
                        if week_offset == 0:
                            game_type = "SF"; semi_final_winners.append(winner); semi_final_losers.append(loser)
                        elif week_offset == 1:
                            if {manager1.nickname, manager2.nickname}.issubset(semi_final_winners): game_type = "1st"
                            else: game_type = "3rd"
                
                all_matchups_data.append({
                    "season": int(season), "week": week, "game_type": game_type,
                    "team1_manager_name": manager1.nickname, "team2_manager_name": manager2.nickname,
                    "team1_score": team1.points, "team2_score": team2.points,
                    "winner_manager_name": winner
                })
    
    output_file = DATA_DIR / "historical_data.json"
    with open(output_file, "w") as f:
        json.dump(all_matchups_data, f, indent=2)
    logging.info(f"\n✅ {output_file} has been built from the local cache.")

if __name__ == "__main__":
    build_historical_data_from_cache()
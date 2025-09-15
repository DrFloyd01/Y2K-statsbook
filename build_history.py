import json
import logging
import pickle
import os # <-- Included as requested

logging.basicConfig(level=logging.INFO, format='%(message)s')

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
    logging.info("Loading raw data from cache (raw_api_cache.pkl)...")
    try:
        with open("raw_api_cache.pkl", "rb") as f:
            raw_data = pickle.load(f)
    except FileNotFoundError:
        logging.error("ERROR: raw_api_cache.pkl not found.")
        return

    all_matchups_data = []
    
    for season, season_data in raw_data.items():
        logging.info(f"--- Processing Season: {season} ---")
        
        settings = season_data.get("settings")
        weeks_data = season_data.get("weeks")

        if not settings or not weeks_data:
            continue

        playoff_start_week = int(settings.playoff_start_week)
        num_playoff_teams = int(settings.num_playoff_teams)
        
        semi_final_winners = []
        semi_final_losers = []

        for week_str, matchups in weeks_data.items():
            week = int(week_str)
            logging.info(f"Processing cached data for {season}, Week {week}...")
            
            semi_final_week_offset = 1 if num_playoff_teams >= 6 else 0
            semi_final_week = playoff_start_week + semi_final_week_offset

            for m in matchups:
                team1, team2 = m.teams[0], m.teams[1]
                
                # Use the helper function to find the primary manager
                manager1 = get_primary_manager(team1, YOUR_NICKNAME)
                manager2 = get_primary_manager(team2, YOUR_NICKNAME)

                game_type = "regular"
                if m.is_playoffs:
                    if m.is_consolation: game_type = "consolation"
                    else:
                        if week == semi_final_week:
                            game_type = "SF"
                            winner_key = m.winner_team_key
                            if team1.team_key == winner_key:
                                semi_final_winners.append(manager1.nickname)
                                semi_final_losers.append(manager2.nickname)
                            else:
                                semi_final_winners.append(manager2.nickname)
                                semi_final_losers.append(manager1.nickname)
                        elif week > semi_final_week:
                            if {manager1.nickname, manager2.nickname}.issubset(semi_final_winners): game_type = "1st"
                            elif {manager1.nickname, manager2.nickname}.issubset(semi_final_losers): game_type = "3rd"
                        else: game_type = "QF"
                
                winner_manager_name = None
                if not m.is_tied:
                    if team1.points > team2.points: winner_manager_name = manager1.nickname
                    else: winner_manager_name = manager2.nickname
                
                all_matchups_data.append({
                    "season": int(season), "week": week, "game_type": game_type,
                    "team1_manager_name": manager1.nickname, "team2_manager_name": manager2.nickname,
                    "team1_score": team1.points, "team2_score": team2.points,
                    "winner_manager_name": winner_manager_name
                })

    with open("historical_data.json", "w") as f:
        json.dump(all_matchups_data, f, indent=2)
    logging.info("\n✅ historical_data.json has been built from the local cache.")

if __name__ == "__main__":
    build_historical_data_from_cache()
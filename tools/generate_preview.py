import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

# --- Directory Setup ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def update_h2h_records(week_results, h2h_records, season, settings):
    """
    Updates the H2H records dictionary with the results from a completed week.
    """
    logging.info(f"Updating H2H records with Week {week_results[0].week} results...")
    
    playoff_start_week = int(settings.playoff_start_week)
    num_playoff_teams = int(settings.num_playoff_teams)

    for matchup in week_results:
        manager1 = matchup.teams[0].managers[0]
        manager2 = matchup.teams[1].managers[0]

        if manager1.nickname == '--hidden--' or manager2.nickname == '--hidden--':
            continue

        key = "-".join(sorted([manager1.nickname, manager2.nickname]))
        if key not in h2h_records:
            continue
        
        # Determine game_type using the same logic as build_history
        game_type = "regular"
        if matchup.is_playoffs:
            if matchup.is_consolation: game_type = "consolation"
            elif matchup.is_third_place: game_type = "3rd"
            else:
                week_offset = matchup.week - playoff_start_week
                if num_playoff_teams >= 6:
                    if week_offset == 0: game_type = "QF"
                    elif week_offset == 1: game_type = "SF"
                    else: game_type = "1st"
                else:
                    if week_offset == 0: game_type = "SF"
                    else: game_type = "1st"

        if game_type == 'consolation':
            continue

        record = h2h_records[key]
        
        winner_name = None
        if not matchup.is_tied:
            winner_name = manager1.nickname if matchup.winner_team_key == matchup.teams[0].team_key else manager2.nickname

        if not winner_name:
            continue

        # Ensure the history lists exist before trying to append to them
        if 'playoff_history' not in record:
            record['playoff_history'] = []
        if 'regular_history' not in record:
            record['regular_history'] = []

        # Determine if manager1 or manager2 in the record won
        is_manager1_winner = (winner_name == record['manager1_name'])

        if game_type in ['QF', 'SF', '1st', '3rd']:
            if is_manager1_winner: record['playoff_wins_1'] += 1
            else: record['playoff_wins_2'] += 1
            record['playoff_history'].append({
                "winner": winner_name, "type": game_type, 
                "season": int(season), "week": matchup.week
            })
        else: # game_type is 'regular'
            if is_manager1_winner: record['reg_wins_1'] += 1
            else: record['reg_wins_2'] += 1
            record['regular_history'].append({
                "winner": winner_name, "type": game_type, 
                "season": int(season), "week": matchup.week
            })
        # Update streak
        if record['streak_holder'] == winner_name:
            record['streak_len'] += 1
        else:
            record['streak_holder'] = winner_name
            record['streak_len'] = 1

        # FIX 2: Use the 'season' variable passed into the function
        record['last_game'] = {"season": int(season), "week": matchup.week}

    return h2h_records

def prepare_preview_data(preview_week, query, standings, h2h_records, season="2025"):
    """
    Prepares the data object for the weekly preview and saves it to a JSON file.
    """
    logging.info(f"Preparing preview data for Week {preview_week}...")
    
    team_data_map = {}
    for team in standings.teams:
        record = team.team_standings.outcome_totals
        team_data_map[team.team_key] = {
            "name": team.name.decode('utf-8'),
            "rank": team.team_standings.rank,
            "record": f"({record.wins}-{record.losses})",
            "manager_name": team.managers[0].nickname
        }

    matchups = query.get_league_matchups_by_week(preview_week)
    
    matchups.sort(key=lambda m: min(
        team_data_map[m.teams[0].team_key]['rank'],
        team_data_map[m.teams[1].team_key]['rank']
    ))

    matchups_data = []
    for matchup in matchups:
        team1_data = team_data_map[matchup.teams[0].team_key]
        team2_data = team_data_map[matchup.teams[1].team_key]
        
        key = "-".join(sorted([team1_data['manager_name'], team2_data['manager_name']]))
        h2h = h2h_records.get(key)
        
        if team1_data['rank'] > team2_data['rank']:
            team1_data, team2_data = team2_data, team1_data

        h2h_data_for_matchup = None
        if h2h:
            if h2h['manager1_name'] == team1_data['manager_name']:
                reg_h2h = f"{h2h['reg_wins_1']}-{h2h['reg_wins_2']}"
                playoff_record_str = f"{h2h['playoff_wins_1']}-{h2h['playoff_wins_2']}"
            else:
                reg_h2h = f"{h2h['reg_wins_2']}-{h2h['reg_wins_1']}"
                playoff_record_str = f"{h2h['playoff_wins_2']}-{h2h['playoff_wins_1']}"
            
            streak_info = "No Streak"
            if h2h.get('streak_holder'):
                streak_holder = h2h['streak_holder']
                streak_len = h2h['streak_len']
                
                # Find all games in the current streak
                streak_games_info = []
                # The history is already sorted chronologically
                for game in reversed(h2h.get('playoff_history', []) + h2h.get('regular_history', [])):
                    if len(streak_games_info) < streak_len and game['winner'] == streak_holder:
                        game_type = game.get('type', f"Wk{game['week']}")
                        season_short = str(game['season'])[-2:]
                        streak_games_info.append(f"{game_type}'{season_short}")
                    elif len(streak_games_info) >= streak_len:
                        break
                streak_info = f"{streak_holder} W{streak_len} ({', '.join(reversed(streak_games_info))})"

            playoff_h2h_display = f"<strong>Playoffs H2H:</strong> {playoff_record_str}"
            if h2h.get('playoff_history'):
                p1_wins = [f"{g['type']}'{str(g['season'])[-2:]}" for g in h2h['playoff_history'] if g['winner'] == h2h['manager1_name']]
                p2_wins = [f"{g['type']}'{str(g['season'])[-2:]}" for g in h2h['playoff_history'] if g['winner'] == h2h['manager2_name']]
                
                if h2h['manager1_name'] == team1_data['manager_name']:
                    wins_str = f" ({team1_data['manager_name']}: {', '.join(p1_wins)})" if p1_wins else ""
                    losses_str = f" ({team2_data['manager_name']}: {', '.join(p2_wins)})" if p2_wins else ""
                else:
                    wins_str = f" ({team1_data['manager_name']}: {', '.join(p2_wins)})" if p2_wins else ""
                    losses_str = f" ({team2_data['manager_name']}: {', '.join(p1_wins)})" if p1_wins else ""

                if wins_str or losses_str:
                    playoff_h2h_display += f"{wins_str}{losses_str}"
            
            h2h_data_for_matchup = {
                "reg_h2h": reg_h2h,
                "streak_info": streak_info,
                "playoff_h2h_display": playoff_h2h_display
            }

        matchups_data.append({
            "team1": team1_data,
            "team2": team2_data,
            "h2h": h2h_data_for_matchup
        })

    # Final data object to be saved
    final_data = {
        "season": season,
        "preview_week": preview_week,
        "matchups": matchups_data
    }

    with open(DATA_DIR / "preview_data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)
    
    logging.info(f"✅ Successfully saved preview data to: {DATA_DIR / 'preview_data.json'}")

def run_preview_process(target_season, preview_week):
    """
    Main orchestrator for the weekly preview generation.
    """
    # --- LOAD DATA ---
    with open(DATA_DIR.parent / "leagues.json", "r") as f: # leagues.json is in root
        all_leagues = json.load(f)
    current_season_config = all_leagues[target_season]
    
    h2h_records_file = DATA_DIR / "h2h_records.json"
    try:
        with open(h2h_records_file, "r") as f:
            h2h_records = json.load(f)
    except FileNotFoundError:
        logging.error("ERROR: h2h_records.json not found. Please run init_h2h_records.py first.")
        return

    query = YahooFantasySportsQuery(
        league_id=current_season_config["league_id"], game_code="nfl", game_id=current_season_config["game_id"],
        yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
        env_file_location=Path("."), save_token_data_to_env_file=True
    )

    # --- UPDATE STATE (The "Look Back" Step) ---
    if preview_week > 1:
        update_week = preview_week - 1
        last_week_results = query.get_league_matchups_by_week(update_week)
        
        if last_week_results and last_week_results[0].status == "postevent":
            settings = query.get_league_settings() # Get settings for the update function
            h2h_records = update_h2h_records(last_week_results, h2h_records, target_season, settings)
            
            with open(h2h_records_file, "w") as f:
                json.dump(h2h_records, f, indent=2)
            logging.info("Successfully updated and saved h2h_records.json.\n")
        else:
            logging.info(f"Week {update_week} results not final yet. Skipping H2H update.\n")

    # --- GENERATE PREVIEW (The "Look Forward" Step) ---
    standings = query.get_league_standings()
    # This now prepares a data file instead of generating HTML
    prepare_preview_data(
        preview_week=preview_week, query=query, standings=standings, 
        h2h_records=h2h_records, season=target_season
    )
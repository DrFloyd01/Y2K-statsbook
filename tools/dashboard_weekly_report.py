import json
import logging
import os
import pickle
from pathlib import Path
from collections import defaultdict
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

def default_alt_standing():
    """Provides a default dictionary for a new manager in alt_standings.
    This is here for pickle compatibility with older cache files."""
    return {'wins': 0, 'losses': 0, 'pf': 0.0}

def calculate_standings_from_matchups(max_week, cache_dir):
    """
    Calculates the "real" league standings up to a specific week by processing
    all cached matchup files. This avoids using live API data for historical reports.
    Returns a map of {manager_nickname: {'rank': rank, 'record': 'W-L'}}.
    """
    records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'pf': 0.0})
    for week in range(1, max_week + 1):
        matchups_file = cache_dir / f"week_{week}_matchups.pkl"
        if not matchups_file.exists(): continue
        with open(matchups_file, "rb") as f:
            matchups = pickle.load(f)
        for m in matchups:
            t1, t2 = m.teams[0], m.teams[1]
            m1, m2 = t1.managers[0].nickname, t2.managers[0].nickname
            records[m1]['pf'] += t1.points
            records[m2]['pf'] += t2.points
            if m.is_tied:
                records[m1]['ties'] += 1; records[m2]['ties'] += 1
            else:
                winner = m1 if m.winner_team_key == t1.team_key else m2
                loser = m2 if winner == m1 else m1
                records[winner]['wins'] += 1; records[loser]['losses'] += 1
    
    sorted_managers = sorted(records.keys(), key=lambda m: (records[m]['wins'], records[m]['pf']), reverse=True)
    return {m: {'rank': i + 1, 'record': f"{records[m]['wins']}-{records[m]['losses']}"} for i, m in enumerate(sorted_managers)}

def process_and_cache_week(week, query, cache_dir):
    """
    Fetches data for a specific week, processes it, and saves it to cache.
    This function is designed to be called in a loop to "catch up" on missed weeks.
    """
    logging.info(f"--- Processing and caching data for Week {week} ---")

    # Define cache files for the week being processed
    matchups_cache_file = cache_dir / f"week_{week}_matchups.pkl"
    alt_standings_cache_file = cache_dir / f"week_{week}_alt_standings.pkl"

    # Fetch and cache matchups
    matchups = query.get_league_matchups_by_week(week)
    if not matchups or matchups[0].status != "postevent":
        logging.warning(f"Week {week} results are not final. Cannot process.")
        return False
    with open(matchups_cache_file, "wb") as f:
        pickle.dump(matchups, f)

    # Load the previous week's alternative standings to build upon
    alt_standings = defaultdict(default_alt_standing)
    if week > 1:
        prev_alt_standings_cache = cache_dir / f"week_{week - 1}_alt_standings.pkl"
        if prev_alt_standings_cache.exists():
            with open(prev_alt_standings_cache, "rb") as f:
                alt_standings = pickle.load(f)
        else:
            # This case should not be hit if weeks are processed sequentially
            logging.error(f"FATAL: Cannot find required cache file: {prev_alt_standings_cache}")
            return False

    # Calculate weekly scores from matchups
    weekly_scores = []
    for matchup in matchups:
        team1_data = matchup.teams[0]
        team2_data = matchup.teams[1]

        weekly_scores.append({
            'manager': team1_data.managers[0].nickname,
            'score': team1_data.points,
        })
        weekly_scores.append({
            'manager': team2_data.managers[0].nickname,
            'score': team2_data.points,
        })

    weekly_scores.sort(key=lambda x: x['score'], reverse=True)

    # Update the running Alternative Universe standings
    num_teams = len(weekly_scores)
    median_index = num_teams // 2
    for i, team in enumerate(weekly_scores):
        manager = team['manager']
        alt_standings[manager]['pf'] += team['score']
        if i < median_index:
            alt_standings[manager]['wins'] += 1
        else:
            alt_standings[manager]['losses'] += 1

    # Save the newly updated alt standings for the *current* processed week
    with open(alt_standings_cache_file, "wb") as f:
        pickle.dump(alt_standings, f)
    
    logging.info(f"--- Successfully cached data for Week {week} ---")
    return True

def prepare_report_data(report_week, season, cache_dir):
    """Generates and prints the full weekly report for a given week."""
    matchups_cache_file = cache_dir / f"week_{report_week}_matchups.pkl"
    alt_standings_cache_file = cache_dir / f"week_{report_week}_alt_standings.pkl"

    # --- Calculate Historical Standings for Deltas ---
    # This is now derived from cached matchups, not a potentially tainted standings file.
    prev_standings_map = {m: d['rank'] for m, d in calculate_standings_from_matchups(report_week - 1, cache_dir).items()} if report_week > 1 else {}
    team_data_map = calculate_standings_from_matchups(report_week, cache_dir)

    # Load previous week's alt standings to calculate rank changes
    prev_alt_rank_map = {}
    if report_week > 1:
        prev_alt_standings_cache = cache_dir / f"week_{report_week - 1}_alt_standings.pkl"
        if prev_alt_standings_cache.exists():
            with open(prev_alt_standings_cache, "rb") as f:
                prev_alt_standings = pickle.load(f)
                # Sort previous alt standings to get ranks
                sorted_prev_alt = sorted(prev_alt_standings.items(), key=lambda item: (item[1]['wins'], item[1]['pf']), reverse=True)
                prev_alt_rank_map = {manager: i + 1 for i, (manager, _) in enumerate(sorted_prev_alt)}

    # Load current week's alt standings
    with open(alt_standings_cache_file, "rb") as f:
        alt_standings = pickle.load(f)
    
    # Load data for the report week (it's guaranteed to exist now)
    logging.info(f"\nGenerating report for Week {report_week}...")
    with open(matchups_cache_file, "rb") as f:
        matchups = pickle.load(f)

    # Re-check that the matchups for the report week are final before proceeding
    if not matchups or matchups[0].status != "postevent":
        logging.info(f"Week {report_week} results are not final yet. Cannot generate report.")
        return

    # Process matchups to get weekly scores and details
    weekly_scores = []
    for matchup in matchups:
        team1_data = matchup.teams[0]
        team2_data = matchup.teams[1]

        winner_nickname = None
        if not matchup.is_tied:
            winner_team = team1_data if matchup.winner_team_key == team1_data.team_key else team2_data
            winner_nickname = winner_team.managers[0].nickname

        # Create one entry for each team with all necessary info
        team1_manager = team1_data.managers[0].nickname
        team2_manager = team2_data.managers[0].nickname

        weekly_scores.append({
            'manager': team1_manager,
            'score': team1_data.points,
            'opponent': team2_manager,
            'is_winner': winner_nickname == team1_manager,
            'is_tied': matchup.is_tied
        })
        weekly_scores.append({
            'manager': team2_manager,
            'score': team2_data.points,
            'opponent': team1_manager,
            'is_winner': winner_nickname == team2_manager,
            'is_tied': matchup.is_tied
        })

    weekly_scores.sort(key=lambda x: x['score'], reverse=True)

    # --- Accolade Calculations ---
    
    top_team = weekly_scores[0]
    losing_teams = [t for t in weekly_scores if not t['is_winner'] and not t['is_tied']]
    highest_scoring_loser = max(losing_teams, key=lambda x: x['score']) if losing_teams else None

    winning_teams = [t for t in weekly_scores if t['is_winner']]
    lowest_scoring_winner = min(winning_teams, key=lambda x: x['score']) if winning_teams else None

    # Margins
    min_margin, smd_details = float('inf'), None
    max_margin, blowout_details = 0, None
    for matchup in matchups:
        if not matchup.is_tied:
            margin = abs(matchup.teams[0].points - matchup.teams[1].points)
            winner_team = [t for t in matchup.teams if t.team_key == matchup.winner_team_key][0]
            winner_manager = winner_team.managers[0].nickname
            loser_manager = matchup.teams[0].managers[0].nickname if winner_manager == matchup.teams[1].managers[0].nickname else matchup.teams[1].managers[0].nickname
            
            if margin < min_margin:
                min_margin = margin
                smd_details = {'manager': loser_manager, 'margin': margin, 'opponent': winner_manager}
            
            if margin > max_margin:
                max_margin = margin
                blowout_details = {'manager': winner_manager, 'margin': margin, 'opponent': loser_manager}
    
    # --- Update and save season-long accolade counts ---
    accolade_counts_file = DATA_DIR / "accolade_counts.json"
    season_accolade_counts = defaultdict(lambda: defaultdict(int))
    if accolade_counts_file.exists():
        with open(accolade_counts_file, "r") as f:
            season_accolade_counts.update({k: defaultdict(int, v) for k, v in json.load(f).items()})

    season_accolade_counts[top_team['manager']]['top_points'] += 1
    if highest_scoring_loser: season_accolade_counts[highest_scoring_loser['manager']]['tough_luck'] += 1
    if lowest_scoring_winner: season_accolade_counts[lowest_scoring_winner['manager']]['luckiest_win'] += 1
    if smd_details: season_accolade_counts[smd_details['manager']]['heartbreak'] += 1
    if blowout_details: season_accolade_counts[blowout_details['manager']]['blowout'] += 1

    # --- Data Preparation ---
    report_data = {"report_week": report_week, "season": season, "alt_standings_rows": [], "accolades": []}

    def get_count_str(manager, accolade_type):
        count = season_accolade_counts[manager].get(accolade_type, 0)
        return f"<span class='count'>({count}x this season)</span>" if count > 0 else ""

    sorted_alt_managers = [m for m, _ in sorted(alt_standings.items(), key=lambda item: (item[1]['wins'], item[1]['pf']), reverse=True)]
    median_index = len(weekly_scores) // 2
    alt_winners_this_week = {team['manager'] for team in weekly_scores[:median_index]}

    for alt_rank, manager in enumerate(sorted_alt_managers, 1):
        alt_data = alt_standings[manager]
        real_data = team_data_map[manager]
        weekly_score_data = next((ws for ws in weekly_scores if ws['manager'] == manager), None)

        prev_alt = prev_alt_rank_map.get(manager, 0)
        alt_delta_val = prev_alt - alt_rank
        alt_delta_str = f"({alt_delta_val:+})" if prev_alt > 0 else "(-)"
        alt_delta_class = "delta-pos" if alt_delta_val > 0 else "delta-neg" if alt_delta_val < 0 else ""

        current_real_rank = real_data.get('rank', 0)
        prev_real = prev_standings_map.get(manager, 0)
        real_delta_val = prev_real - current_real_rank
        real_delta_str = f"({real_delta_val:+})" if prev_real > 0 and current_real_rank > 0 else "(-)"
        real_delta_class = "delta-pos" if real_delta_val > 0 else "delta-neg" if real_delta_val < 0 else ""

        alt_win_marker = "🌌" if manager in alt_winners_this_week else ""
        real_win_marker = "✅" if weekly_score_data and weekly_score_data['is_winner'] else ""

        report_data['alt_standings_rows'].append({
            "alt_rank": alt_rank,
            "alt_delta_class": alt_delta_class,
            "alt_delta_str": alt_delta_str,
            "alt_win_marker": alt_win_marker,
            "current_real_rank": current_real_rank,
            "real_delta_class": real_delta_class,
            "real_delta_str": real_delta_str,
            "real_win_marker": real_win_marker,
            "manager": manager,
            "weekly_score": weekly_score_data['score'],
            "total_pf": alt_data['pf'],
            "alt_record": f"{alt_data['wins']}-{alt_data['losses']}",
            "real_record": real_data['record']
        })

    report_data['accolades'].append(f"<strong>🌋 Top Points:</strong> {top_team['manager']} ({top_team['score']:.2f} vs {top_team['opponent']}) {get_count_str(top_team['manager'], 'top_points')}")
    if highest_scoring_loser:
        report_data['accolades'].append(f"<strong>💔 Tough Luck Loss:</strong> {highest_scoring_loser['manager']} ({highest_scoring_loser['score']:.2f} vs {highest_scoring_loser['opponent']}) {get_count_str(highest_scoring_loser['manager'], 'tough_luck')}")
    if lowest_scoring_winner:
        report_data['accolades'].append(f"<strong>🍀 Luckiest Win:</strong> {lowest_scoring_winner['manager']} ({lowest_scoring_winner['score']:.2f} vs {lowest_scoring_winner['opponent']}) {get_count_str(lowest_scoring_winner['manager'], 'luckiest_win')}")
    if smd_details:
        report_data['accolades'].append(f"<strong>🤏 Heartbreak Loss:</strong> {smd_details['manager']} (lost by {smd_details['margin']:.2f} to {smd_details['opponent']}) {get_count_str(smd_details['manager'], 'heartbreak')}")
    if blowout_details:
        report_data['accolades'].append(f"<strong>💥 Biggest Blowout:</strong> {blowout_details['manager']} (won by {blowout_details['margin']:.2f} over {blowout_details['opponent']}) {get_count_str(blowout_details['manager'], 'blowout')}")

    output_filename = DATA_DIR / "report_card_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    with open(accolade_counts_file, "w") as f:
        json.dump(season_accolade_counts, f, indent=2)
    logging.info(f"✅ Successfully updated {accolade_counts_file}")
    
    logging.info(f"✅ Successfully saved report card data to: {output_filename.name}")

def run_report_process(target_season, last_completed_week):
    """ 
    Main orchestrator for the weekly report. Ensures all past weeks are cached
    before generating a report for the most recently completed week.
    """
    # --- LOAD DATA ---
    try:
        with open(DATA_DIR.parent / "leagues.json", "r") as f: # leagues.json is in root
            all_leagues = json.load(f)
    except FileNotFoundError:
        logging.error("ERROR: leagues.json not found. Please run build_history.py first.")
        return
        
    current_season_config = all_leagues[target_season]

    query = YahooFantasySportsQuery(
        league_id=current_season_config["league_id"], game_code="nfl", game_id=current_season_config["game_id"],
        yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
        env_file_location=Path("."), save_token_data_to_env_file=True
    )
    
    if last_completed_week == 0:
        logging.info("No weeks have been completed yet. Skipping report generation.")
        return
    
    # --- Catch-up Caching Loop ---
    # Ensures all weeks from 1 up to the last completed week are cached.
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    for week_to_check in range(1, last_completed_week + 1):
        # Only process if the final matchup data isn't already cached.
        if not (cache_dir / f"week_{week_to_check}_matchups.pkl").exists():
            logging.info(f"Cache for Week {week_to_check} not found. Processing now...")
            if not process_and_cache_week(week_to_check, query, cache_dir):
                logging.error(f"Failed to process week {week_to_check}. Aborting report generation.")
                return

    # --- Generate Report ---
    # After ensuring all necessary weeks are cached, generate the report for the last completed week.
    prepare_report_data(report_week=last_completed_week, season=target_season, cache_dir=cache_dir)

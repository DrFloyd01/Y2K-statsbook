import json
import logging
import os
import pickle
from pathlib import Path
from collections import defaultdict
import statistics
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

def default_standing_factory():
    """
    Provides a default dictionary for team standings.

    Returns:
        dict: A dictionary with default values for team standings.
    """
    return {'wins': 0, 'losses': 0, 'ties': 0, 'pf': 0.0, 'pa': 0.0}

default_alt_standing_factory = default_standing_factory

def calculate_standings_from_matchups(max_week, cache_dir):
    """
    Calculates standings from cached matchup data.

    Args:
        max_week (int): The maximum week to process.
        cache_dir (Path): The path to the cache directory.

    Returns:
        dict: A dictionary of team standings.
    """
    records = defaultdict(default_standing_factory)
    for week in range(1, max_week + 1):
        matchups_file = cache_dir / f"week_{week}_matchups.pkl"
        if not matchups_file.exists(): continue
        with open(matchups_file, "rb") as f:
            matchups = pickle.load(f)
        for m in matchups:
            t1, t2 = m.teams[0], m.teams[1]
            m1, m2 = t1.managers[0].nickname, t2.managers[0].nickname
            records[m1]['pf'] += t1.points; records[m2]['pf'] += t2.points
            records[m1]['pa'] += t2.points; records[m2]['pa'] += t1.points
            if m.is_tied:
                records[m1]['ties'] += 1; records[m2]['ties'] += 1
            else:
                winner = m1 if m.winner_team_key == t1.team_key else m2
                loser = m2 if winner == m1 else m1
                records[winner]['wins'] += 1; records[loser]['losses'] += 1
    
    sorted_managers = sorted(records.keys(), key=lambda m: (records[m]['wins'], records[m]['pf']), reverse=True)
    standings = {}
    for i, manager_name in enumerate(sorted_managers):
        standings[manager_name] = {
            'rank': i + 1,
            'record': f"{records[manager_name]['wins']}-{records[manager_name]['losses']}",
            'pf': records[manager_name]['pf'],
            'pa': records[manager_name]['pa']
        }
    return standings

def process_and_cache_week(week, query, cache_dir):
    """
    Processes and caches data for a given week.

    Args:
        week (int): The week to process.
        query (YahooFantasySportsQuery): An authenticated yfpy query object.
        cache_dir (Path): The path to the cache directory.

    Returns:
        bool: True if the week was processed successfully, False otherwise.
    """
    logging.info(f"--- Processing and caching data for Week {week} ---")
    matchups_cache_file = cache_dir / f"week_{week}_matchups.pkl"
    alt_standings_cache_file = cache_dir / f"week_{week}_alt_standings.pkl"
    matchups = query.get_league_matchups_by_week(week)
    if not matchups or matchups[0].status != "postevent":
        logging.warning(f"Week {week} results are not final. Cannot process.")
        return False
    with open(matchups_cache_file, "wb") as f:
        pickle.dump(matchups, f)
    alt_standings = defaultdict(default_standing_factory)
    if week > 1:
        prev_alt_standings_cache = cache_dir / f"week_{week - 1}_alt_standings.pkl"
        if prev_alt_standings_cache.exists():
            with open(prev_alt_standings_cache, "rb") as f:
                alt_standings = pickle.load(f)
        else:
            logging.error(f"FATAL: Cannot find required cache file: {prev_alt_standings_cache}")
            return False
    weekly_scores = []
    for matchup in matchups:
        team1_data = matchup.teams[0]; team2_data = matchup.teams[1]
        weekly_scores.append({'manager': team1_data.managers[0].nickname, 'score': team1_data.points})
        weekly_scores.append({'manager': team2_data.managers[0].nickname, 'score': team2_data.points})
    weekly_scores.sort(key=lambda x: x['score'], reverse=True)
    num_teams = len(weekly_scores)
    median_index = num_teams // 2
    for i, team in enumerate(weekly_scores):
        manager = team['manager']
        alt_standings[manager]['pf'] += team['score']
        if i < median_index:
            alt_standings[manager]['wins'] += 1
        else:
            alt_standings[manager]['losses'] += 1
    with open(alt_standings_cache_file, "wb") as f:
        pickle.dump(alt_standings, f)
    if alt_standings_cache_file.stat().st_size == 0:
        raise EOFError(f"FATAL: Created an empty cache file: {alt_standings_cache_file}")
    logging.info(f"--- Successfully cached data for Week {week} ---")
    return True

def calculate_weekly_accolades(week, cache_dir):
    """
    Calculates weekly accolades from cached matchup data.

    Args:
        week (int): The week to process.
        cache_dir (Path): The path to the cache directory.

    Returns:
        list: A list of weekly accolades.
    """
    matchups_cache_file = cache_dir / f"week_{week}_matchups.pkl"
    if not matchups_cache_file.exists(): return None
    with open(matchups_cache_file, "rb") as f:
        matchups = pickle.load(f)
    if not matchups or matchups[0].status != "postevent": return None

    weekly_scores = []
    for matchup in matchups:
        team1_data = matchup.teams[0]; team2_data = matchup.teams[1]
        winner_nickname = None
        if not matchup.is_tied:
            winner_team = team1_data if matchup.winner_team_key == team1_data.team_key else team2_data
            winner_nickname = winner_team.managers[0].nickname
        team1_manager = team1_data.managers[0].nickname; team2_manager = team2_data.managers[0].nickname
        weekly_scores.append({'manager': team1_manager, 'score': team1_data.points, 'opponent': team2_manager, 'is_winner': winner_nickname == team1_manager, 'is_tied': matchup.is_tied})
        weekly_scores.append({'manager': team2_manager, 'score': team2_data.points, 'opponent': team1_manager, 'is_winner': winner_nickname == team2_manager, 'is_tied': matchup.is_tied})
    weekly_scores.sort(key=lambda x: x['score'], reverse=True)

    top_team = weekly_scores[0]
    losing_teams = [t for t in weekly_scores if not t['is_winner'] and not t['is_tied']]
    highest_scoring_loser = max(losing_teams, key=lambda x: x['score']) if losing_teams else None
    winning_teams = [t for t in weekly_scores if t['is_winner']]
    lowest_scoring_winner = min(winning_teams, key=lambda x: x['score']) if winning_teams else None
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

    accolade_definitions = [
        {'title': "🌋 Top Point Scorer", 'data': top_team, 'key': "top_points", 'field': "score", 'comparison': "gt", 'details_template': "{score:.2f} pts vs {opponent}"},
        {'title': "💔 Highest Scoring Loser", 'data': highest_scoring_loser, 'key': "highest_scoring_loss", 'field': "score", 'comparison': "gt", 'details_template': "{score:.2f} pts in loss vs {opponent}"},
        {'title': "🍀 Lowest Scoring Winner", 'data': lowest_scoring_winner, 'key': "lowest_scoring_win", 'field': "score", 'comparison': "lt", 'details_template': "{score:.2f} pts in win vs {opponent}"},
        {'title': "💥 Blowout of the Week", 'data': blowout_details, 'key': "blowout_win", 'field': "margin", 'comparison': "gt", 'details_template': "{margin:.2f} pt margin vs {opponent}"},
        {'title': "🤏 Heartbreak of the Week", 'data': smd_details, 'key': "smallest_margin_defeat", 'field': "margin", 'comparison': "lt", 'details_template': "{margin:.2f} pt margin vs {opponent}"}
    ]
    
    weekly_accolades = []
    for accolade in accolade_definitions:
        if accolade['data']:
            weekly_accolades.append({"title": accolade["title"],"key": accolade["key"],"field": accolade["field"],"comparison": accolade["comparison"],"details_template": accolade["details_template"],"winner_data": accolade['data']})
    return weekly_accolades

def prepare_report_data(report_week, season, cache_dir, seasonal_accolades, all_scores_by_manager):
    """
    Prepares the data for the weekly report.

    Args:
        report_week (int): The week to report on.
        season (str): The season to report on.
        cache_dir (Path): The path to the cache directory.
        seasonal_accolades (dict): A dictionary of seasonal accolades.
        all_scores_by_manager (dict): A dictionary of all scores by manager.
    """
    logging.info(f"\nGenerating report for Week {report_week}...")
    report_data = {"report_week": report_week, "season": season, "alt_standings_rows": [], "accolades": [], "manager_stdevs": {}}

    try:
        with open(DATA_DIR / "accolades_data.json", "r") as f:
            accolades_data = json.load(f)
        per_season_records = accolades_data.get('per_season_records', {}).get(str(season), {})
        all_time_records = accolades_data.get('all_time_records', {})
    except FileNotFoundError:
        per_season_records, all_time_records = {}, {}

    # Calculate standard deviation for each manager
    for manager, scores in all_scores_by_manager.items():
        if len(scores) > 1:
            stdev = statistics.stdev(scores)
            report_data["manager_stdevs"][manager] = f"±{stdev:.2f}"

    current_week_accolades = seasonal_accolades.get(str(season), {}).get(str(report_week), [])

    for accolade in current_week_accolades:
        history_for_accolade = {w: winner for w, accolades_in_week in seasonal_accolades.get(str(season), {}).items() for a in accolades_in_week if a['title'] == accolade['title'] for _, winner in a.items() if _ == 'winner_data'}
        manager_wins = defaultdict(list)
        for week, winner_data in history_for_accolade.items():
            manager_wins[winner_data['manager']].append(f"Wk{week}")
        sorted_managers = sorted(manager_wins.items(), key=lambda item: (len(item[1]), -min(int(w.replace('Wk','')) for w in item[1])), reverse=True)
        summary_parts = [f"{manager} ({','.join(sorted(weeks, key=lambda w: int(w.replace('Wk',''))))})" for manager, weeks in sorted_managers]
        summary_string = "; ".join(summary_parts)

        record_status = None
        data = accolade['winner_data']
        current_value = data[accolade['field']]
        all_time_list = all_time_records.get(accolade['key'], [])
        # Check for a new record, but only if all_time_records were successfully loaded.
        # The `and all_time_records` check prevents false positives if the file is missing.
        is_top_3_contender = len(all_time_list) < 3 or any((accolade['comparison'] == 'gt' and current_value > r[accolade['field']]) or (accolade['comparison'] == 'lt' and current_value < r[accolade['field']]) for r in all_time_list)
        if all_time_records and is_top_3_contender:
            record_status = f"New All-Time Top 3!"
        season_record = per_season_records.get(accolade['key'], {})
        if not record_status and season_record and 'manager' in season_record and ((accolade['comparison'] == 'gt' and current_value > season_record[accolade['field']]) or (accolade['comparison'] == 'lt' and current_value < season_record[accolade['field']])):
            record_status = f"New {season} Season Record!"

        report_data['accolades'].append({
            "title": accolade['title'], "manager": data['manager'], "details": accolade['details_template'].format(**data), "record_status": record_status, "summary": summary_string
        })

    prev_standings_map = {m: d['rank'] for m, d in calculate_standings_from_matchups(report_week - 1, cache_dir).items()} if report_week > 1 else {}
    team_data_map = calculate_standings_from_matchups(report_week, cache_dir)
    with open(cache_dir / f"week_{report_week}_alt_standings.pkl", "rb") as f:
        alt_standings = pickle.load(f)
    with open(cache_dir / f"week_{report_week}_matchups.pkl", "rb") as f:
        matchups = pickle.load(f)
    weekly_scores = []
    for matchup in matchups:
        team1_data = matchup.teams[0]; team2_data = matchup.teams[1]
        winner_nickname = None
        if not matchup.is_tied:
            winner_team = team1_data if matchup.winner_team_key == team1_data.team_key else team2_data
            winner_nickname = winner_team.managers[0].nickname
        weekly_scores.append({'manager': team1_data.managers[0].nickname, 'score': team1_data.points, 'is_winner': winner_nickname == team1_data.managers[0].nickname})
        weekly_scores.append({'manager': team2_data.managers[0].nickname, 'score': team2_data.points, 'is_winner': winner_nickname == team2_data.managers[0].nickname})
    weekly_scores.sort(key=lambda x: x['score'], reverse=True)
    prev_alt_rank_map = {}
    if report_week > 1:
        with open(cache_dir / f"week_{report_week - 1}_alt_standings.pkl", "rb") as f:
            prev_alt_standings = pickle.load(f)
            sorted_prev_alt = sorted(prev_alt_standings.items(), key=lambda item: (item[1]['wins'], item[1]['pf']), reverse=True)
            prev_alt_rank_map = {manager: i + 1 for i, (manager, _) in enumerate(sorted_prev_alt)}
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
            "stdev": report_data["manager_stdevs"].get(manager, "N/A"),
            "alt_rank": alt_rank, "alt_delta_class": alt_delta_class, "alt_delta_str": alt_delta_str, "alt_win_marker": alt_win_marker,
            "current_real_rank": current_real_rank, "real_delta_class": real_delta_class, "real_delta_str": real_delta_str, "real_win_marker": real_win_marker,
            "manager": manager, "weekly_score": weekly_score_data['score'],
            "alt_pf": alt_data['pf'], "real_pf": real_data.get('pf', 0.0), "real_pa": real_data.get('pa', 0.0),
            "alt_record": f"{alt_data['wins']}-{alt_data['losses']}", "real_record": real_data['record']
        })

    output_filename = DATA_DIR / "report_card_data.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    logging.info(f"✅ Successfully saved report card data to: {output_filename.name}")

def run_report_process(target_season, last_completed_week):
    """
    Runs the weekly report process.

    Args:
        target_season (str): The season to process.
        last_completed_week (int): The last completed week of the season.
    """
    try:
        with open(DATA_DIR.parent / "leagues.json", "r") as f:
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
    
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    all_scores_by_manager = defaultdict(list)
    seasonal_accolades = {str(target_season): {}}
    for week in range(1, last_completed_week + 1):
        week_matchups_file = cache_dir / f"week_{week}_matchups.pkl"
        if not week_matchups_file.exists():
            if not process_and_cache_week(week, query, cache_dir):
                logging.error(f"Failed to process week {week} for history. Aborting report generation.")
                return
        
        # Collect all scores for standard deviation calculation
        with open(week_matchups_file, "rb") as f:
            matchups = pickle.load(f)
        for m in matchups:
            for team in m.teams:
                all_scores_by_manager[team.managers[0].nickname].append(team.points)

        weekly_accolades = calculate_weekly_accolades(week, cache_dir)
        if weekly_accolades:
            seasonal_accolades[str(target_season)][str(week)] = weekly_accolades
    
    seasonal_accolades_file = DATA_DIR / "seasonal_accolade_history.json"
    with open(seasonal_accolades_file, "w") as f:
        json.dump(seasonal_accolades, f, indent=2)
    logging.info(f"✅ Successfully built and saved seasonal accolade history.")

    prepare_report_data(report_week=last_completed_week, season=target_season, cache_dir=cache_dir, seasonal_accolades=seasonal_accolades, all_scores_by_manager=all_scores_by_manager)
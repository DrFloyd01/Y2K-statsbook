import json
import logging
import os
import traceback
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from yfpy.query import YahooFantasySportsQuery

# --- Setup and Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO)

YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

LEAGUE_ID = "1286518"
GAME_ID = 380

def process_week(query, week):
    """
    Fetches data and calculates accolades for a single week.
    Returns a dictionary with the weekly report.
    """
    try:
        matchups = query.get_league_matchups_by_week(week)
        
        weekly_scores = []
        for matchup in matchups:
            for team_data in matchup.teams:
                if matchup.is_tied:
                    is_winner, is_loss = False, False
                else:
                    is_winner = (matchup.winner_team_key == team_data.team_key)
                    is_loss = not is_winner

                opponent_data = next(t for t in matchup.teams if t.team_key != team_data.team_key)
                
                weekly_scores.append({
                    # FIX: Decode name from bytes and use .points for the score
                    'name': team_data.name.decode('utf-8'),
                    'score': float(team_data.points),
                    'is_winner': is_winner,
                    'is_loss': is_loss,
                    'opponent_name': opponent_data.name.decode('utf-8')
                })
        
        sorted_scores = sorted(weekly_scores, key=lambda x: x['score'], reverse=True)
        
        # Accolade Calculations
        num_teams = len(weekly_scores)
        top_half_cutoff = num_teams // 2
        alternative_universe_winners = [team['name'] for team in sorted_scores[:top_half_cutoff]]
        top_points_team = sorted_scores[0]
        
        losing_teams = [team for team in weekly_scores if team['is_loss']]
        highest_scoring_loss = max(losing_teams, key=lambda x: x['score']) if losing_teams else None
        
        smallest_margin_team = None
        min_margin = float('inf')
        if losing_teams:
            for team in losing_teams:
                opponent_score = next(t['score'] for t in weekly_scores if t['name'] == team['opponent_name'])
                margin = opponent_score - team['score']
                if margin < min_margin:
                    min_margin = margin
                    smallest_margin_team = team
        
        winning_teams = [team for team in weekly_scores if team['is_winner']]
        lowest_scoring_win = min(winning_teams, key=lambda x: x['score']) if winning_teams else None

        # --- Report Generation ---
        report = {
            "week": week,
            "alternative_universe_winners": alternative_universe_winners,
            "top_points": top_points_team,
            "highest_scoring_loss": highest_scoring_loss,
            "smallest_margin_of_defeat": smallest_margin_team,
            "lowest_scoring_win": lowest_scoring_win,
            "all_scores": sorted_scores
        }
        return report
    except Exception as e:
        logging.error(f"An error occurred processing week {week}: {e}")
        return None

def calculate_season_summary(all_weekly_reports, team_names):
    """
    Aggregates weekly reports into a season summary.
    """
    # Initialize a structure to hold season totals for each team
    season_stats = {name: defaultdict(int) for name in team_names}

    for report in all_weekly_reports:
        # Tally Alternative Universe Wins
        for winner_name in report['alternative_universe_winners']:
            season_stats[winner_name]['alternative_universe_wins'] += 1
        
        # Tally Accolades
        if report['top_points']:
            season_stats[report['top_points']['name']]['top_points_weeks'] += 1
        if report['highest_scoring_loss']:
            season_stats[report['highest_scoring_loss']['name']]['highest_scoring_loss_weeks'] += 1
        if report['smallest_margin_of_defeat']:
            season_stats[report['smallest_margin_of_defeat']['name']]['smallest_margin_defeat_weeks'] += 1
        if report['lowest_scoring_win']:
            season_stats[report['lowest_scoring_win']['name']]['lowest_scoring_win_weeks'] += 1

    # Format the final report for printing
    summary = {
        "Alternative Universe Standings": sorted(
            [{'team': name, 'wins': stats['alternative_universe_wins']} for name, stats in season_stats.items()],
            key=lambda x: x['wins'], reverse=True
        ),
        "Accolade Leaderboard": {
            "Most Top Point Weeks": sorted(
                [{'team': name, 'count': stats['top_points_weeks']} for name, stats in season_stats.items()],
                key=lambda x: x['count'], reverse=True
            ),
            "Most Highest-Scoring Losses (Tough Luck Award)": sorted(
                [{'team': name, 'count': stats['highest_scoring_loss_weeks']} for name, stats in season_stats.items()],
                key=lambda x: x['count'], reverse=True
            ),
             "Most Smallest-Margin Defeats (Heartbreak Award)": sorted(
                [{'team': name, 'count': stats['smallest_margin_defeat_weeks']} for name, stats in season_stats.items()],
                key=lambda x: x['count'], reverse=True
            ),
            "Most Lowest-Scoring Wins (Win is a Win Award)": sorted(
                [{'team': name, 'count': stats['lowest_scoring_win_weeks']} for name, stats in season_stats.items()],
                key=lambda x: x['count'], reverse=True
            )
        }
    }
    return summary


def main():
    """
    Main function to run the full season analysis.
    """
    query = YahooFantasySportsQuery(
        league_id=LEAGUE_ID, game_code="nfl", game_id=GAME_ID,
        yahoo_consumer_key=YAHOO_CONSUMER_KEY, yahoo_consumer_secret=YAHOO_CONSUMER_SECRET,
        env_file_location=Path("."), save_token_data_to_env_file=True
    )

    print("Fetching league settings...")
    settings = query.get_league_settings()
    end_week = int(settings.playoff_start_week) - 1
    print(f"Regular season runs for {end_week} weeks.")

    teams = query.get_league_teams()
    team_names = [t.name.decode('utf-8') for t in teams]
    
    all_weekly_reports = []
    for week in range(1, end_week):
        print(f"Processing Week {week}...")
        weekly_report = process_week(query, week)
        if weekly_report:
            all_weekly_reports.append(weekly_report)
    
    print("\nAll weeks processed. Calculating season summary...")
    season_summary = calculate_season_summary(all_weekly_reports, team_names)
    
    print("\n--- Y2K Fantasy Football Season Report ---")
    print(json.dumps(season_summary, indent=4))
    
    # Save the raw weekly data to a file for your records
    with open("all_weekly_reports.json", "w") as f:
        json.dump(all_weekly_reports, f, indent=4)
    print("\nFull weekly data saved to all_weekly_reports.json")

if __name__ == "__main__":
    main()
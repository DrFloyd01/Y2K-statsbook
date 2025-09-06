import json
import logging
import os
from yfpy.query import YahooFantasySportsQuery

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# User-specific configuration (using environment variables)
# Make sure your .env file is loaded and contains these variables.
# For example:
# YAHOO_CONSUMER_KEY="<YOUR_CONSUMER_KEY>"
# YAHOO_CONSUMER_SECRET="<YOUR_CONSUMER_SECRET>"
YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

LEAGUE_ID = "1286518"  # Your league ID for the 2018 season
GAME_ID = 380  # The game ID for the 2018 NFL season
WEEK = 1  # The week you want to analyze

def generate_weekly_report(league_id, game_id, week, consumer_key, consumer_secret):
    """
    Generates a weekly fantasy football report with unique statistics.

    Args:
        league_id (str): The Yahoo Fantasy Sports league ID.
        game_id (int): The Yahoo game ID for the season.
        week (int): The week number to analyze.
        consumer_key (str): Your Yahoo Developer Network consumer key.
        consumer_secret (str): Your Yahoo Developer Network consumer secret.

    Returns:
        dict: A dictionary containing the weekly report data.
    """
    try:
        # Initialize the query object. This will handle OAuth authentication.
        query = YahooFantasySportsQuery(
            league_id=league_id,
            game_code="nfl",
            game_id=game_id,
            yahoo_consumer_key=consumer_key,
            yahoo_consumer_secret=consumer_secret,
            env_var_fallback=False
        )

        # Get the matchups for the specified week
        matchups = query.get_league_matchups(week)
        
        # --- Data Extraction and Processing ---
        
        # Get all team scores for the week and store in a list of dictionaries
        weekly_scores = []
        for matchup in matchups:
            for team_data in [matchup.team1, matchup.team2]:
                weekly_scores.append({
                    'name': team_data.name,
                    'score': float(team_data.team_points.total),
                    'is_winner': team_data.is_winner,
                    'is_loss': team_data.is_loss,
                    'opponent_name': matchup.team1.name if team_data.team_id == matchup.team2.team_id else matchup.team2.name
                })
        
        # Sort the scores from highest to lowest
        sorted_scores = sorted(weekly_scores, key=lambda x: x['score'], reverse=True)
        
        # --- Accolade Calculations ---
        
        # 1. Alternative Universe Wins (Top Half of the league)
        num_teams = len(weekly_scores)
        top_half_cutoff = num_teams // 2
        alternative_universe_winners = [team['name'] for team in sorted_scores[:top_half_cutoff]]
        
        # 2. Top Points for the week
        top_points_team = sorted_scores[0]
        
        # 3. Highest Scoring Loss
        losing_teams = [team for team in weekly_scores if team['is_loss']]
        highest_scoring_loss = max(losing_teams, key=lambda x: x['score'])
        
        # 4. Smallest Margin of Defeat
        smallest_margin_team = None
        min_margin = float('inf')
        for team in losing_teams:
            opponent_score = next(t['score'] for t in weekly_scores if t['name'] == team['opponent_name'])
            margin = opponent_score - team['score']
            if margin < min_margin:
                min_margin = margin
                smallest_margin_team = team
        
        # 5. Lowest Scoring Win
        winning_teams = [team for team in weekly_scores if team['is_winner']]
        lowest_scoring_win = min(winning_teams, key=lambda x: x['score'])

        # --- Report Generation ---
        report = {
            "week": week,
            "alternative_universe_winners": alternative_universe_winners,
            "top_points": {
                "team": top_points_team['name'],
                "score": top_points_team['score']
            },
            "highest_scoring_loss": {
                "team": highest_scoring_loss['name'],
                "score": highest_scoring_loss['score']
            },
            "smallest_margin_of_defeat": {
                "team": smallest_margin_team['name'],
                "score": smallest_margin_team['score'],
                "margin": round(min_margin, 2)
            },
            "lowest_scoring_win": {
                "team": lowest_scoring_win['name'],
                "score": lowest_scoring_win['score']
            },
            "all_scores": sorted_scores
        }
        
        # Pretty print the report
        print(json.dumps(report, indent=4))
        
        return report

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

# To run the script, replace the placeholder values with your league info.
# This example will run for Week 1 of the 2018 season.
if __name__ == "__main__":
    report_data = generate_weekly_report(
        league_id=LEAGUE_ID,
        game_id=GAME_ID,
        week=WEEK,
        consumer_key=YAHOO_CONSUMER_KEY,
        consumer_secret=YAHOO_CONSUMER_SECRET
    )

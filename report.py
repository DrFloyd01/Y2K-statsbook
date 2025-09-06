import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv  # <<< CHANGE: Import dotenv
from yfpy.query import YahooFantasySportsQuery

# --- Setup and Configuration ---

# Load environment variables from your .env file
load_dotenv()  # <<< CHANGE: Load the .env file

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# Your .env file should contain your consumer key and secret
YAHOO_CONSUMER_KEY = os.environ.get("YAHOO_CONSUMER_KEY")
YAHOO_CONSUMER_SECRET = os.environ.get("YAHOO_CONSUMER_SECRET")

# --- League Parameters ---
LEAGUE_ID = "1286518"  # Your league ID for the 2018 season
GAME_ID = 380          # The game ID for the 2018 NFL season
WEEK = 1               # The week you want to analyze


def generate_weekly_report(league_id, game_id, week, consumer_key, consumer_secret):
    """
    Generates a weekly fantasy football report with unique statistics.
    """
    try:
        # Initialize the query object. This will handle OAuth authentication.
        # With dotenv loaded, this will now properly save/load the token from your .env file.
        query = YahooFantasySportsQuery(
            league_id=league_id,
            game_code="nfl",
            game_id=game_id,
            yahoo_consumer_key=consumer_key,
            yahoo_consumer_secret=consumer_secret,
            env_file_location=Path("."),
            save_token_data_to_env_file=True
        )

        # Get the matchups for the specified week
        matchups = query.get_league_matchups_by_week(week)
        
        # --- Data Extraction and Processing ---

        weekly_scores = []
        for matchup in matchups:
            for team_data in matchup.teams:
                # <<< FINAL FIX: Check for a tie first, otherwise the non-winner is the loser.
                if matchup.is_tied:
                    is_winner = False
                    is_loss = False
                else:
                    is_winner = (matchup.winner_team_key == team_data.team_key)
                    is_loss = not is_winner  # If you're not the winner, you're the loser.

                opponent_data = next(t for t in matchup.teams if t.team_key != team_data.team_key)
                
                weekly_scores.append({
                    'name': team_data.name,
                    'score': float(team_data.points),
                    'is_winner': is_winner,
                    'is_loss': is_loss,
                    'opponent_name': opponent_data.name
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
        # Handle cases with no losses (e.g., ties, though rare)
        highest_scoring_loss = max(losing_teams, key=lambda x: x['score']) if losing_teams else None
        
        # 4. Smallest Margin of Defeat
        smallest_margin_team = None
        min_margin = float('inf')
        if losing_teams:
            for team in losing_teams:
                # Find the opponent's score to calculate the margin
                opponent_score = next(t['score'] for t in weekly_scores if t['name'] == team['opponent_name'])
                margin = opponent_score - team['score']
                if margin < min_margin:
                    min_margin = margin
                    smallest_margin_team = team
        
        # 5. Lowest Scoring Win
        winning_teams = [team for team in weekly_scores if team['is_winner']]
        # Handle cases with no winners
        lowest_scoring_win = min(winning_teams, key=lambda x: x['score']) if winning_teams else None

        # --- Report Generation ---
        report = {
            "week": week,
            "alternative_universe_winners": alternative_universe_winners,
            "top_points": {
                "team": top_points_team['name'],
                "score": top_points_team['score']
            },
            # Handle cases where accolades might not apply (e.g., no losses)
            "highest_scoring_loss": {
                "team": highest_scoring_loss['name'] if highest_scoring_loss else "N/A",
                "score": highest_scoring_loss['score'] if highest_scoring_loss else 0
            },
            "smallest_margin_of_defeat": {
                "team": smallest_margin_team['name'] if smallest_margin_team else "N/A",
                "score": smallest_margin_team['score'] if smallest_margin_team else 0,
                "margin": round(min_margin, 2) if min_margin != float('inf') else 0
            },
            "lowest_scoring_win": {
                "team": lowest_scoring_win['name'] if lowest_scoring_win else "N/A",
                "score": lowest_scoring_win['score'] if lowest_scoring_win else 0
            },
            "all_scores": sorted_scores
        }
        
        # Pretty print the report
        print(json.dumps(report, indent=4))
        
        return report

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # Add more detailed error info for debugging
        import traceback
        traceback.print_exc()
        return None

# --- Main Execution ---
if __name__ == "__main__":
    report_data = generate_weekly_report(
        league_id=LEAGUE_ID,
        game_id=GAME_ID,
        week=WEEK,
        consumer_key=YAHOO_CONSUMER_KEY,
        consumer_secret=YAHOO_CONSUMER_SECRET
    )
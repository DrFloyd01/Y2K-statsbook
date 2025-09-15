import json
import logging
import os
import traceback
import statistics
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

def process_week(query, week, standings):
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
                    'name': team_data.name.decode('utf-8'),
                    'score': float(team_data.points),
                    'is_winner': is_winner,
                    'is_loss': is_loss,
                    'opponent_name': opponent_data.name.decode('utf-8')
                })
        
        sorted_scores = sorted(weekly_scores, key=lambda x: x['score'], reverse=True)
        
        # --- Accolade Calculations ---
        
        # Basic Accolades
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
        
        # New Accolades
        # 1. Blowout of the Week
        blowout = {'margin': 0, 'winner': None, 'loser': None, 'winner_score': 0, 'loser_score': 0}
        for team in weekly_scores:
            if team['is_winner']:
                opponent_score = next(t['score'] for t in weekly_scores if t['name'] == team['opponent_name'])
                margin = team['score'] - opponent_score
                if margin > blowout['margin']:
                    blowout['margin'] = round(margin, 2)
                    blowout['winner'] = team['name']
                    blowout['loser'] = team['opponent_name']
                    blowout['winner_score'] = team['score']
                    blowout['loser_score'] = opponent_score

        # 2. Giant Killer Award
        team_ranks = {t.name.decode('utf-8'): t.team_standings.rank for t in standings.teams}
        giant_killer = {'rank_diff': 0, 'winner': None, 'loser': None}
        for team in weekly_scores:
            if team['is_winner']:
                winner_rank = team_ranks.get(team['name'], 0)
                loser_rank = team_ranks.get(team['opponent_name'], 0)
                if winner_rank > loser_rank:
                    rank_diff = winner_rank - loser_rank
                    if rank_diff > giant_killer['rank_diff']:
                        giant_killer['rank_diff'] = rank_diff
                        giant_killer['winner'] = f"{team['name']} (#{winner_rank})"
                        giant_killer['loser'] = f"{team['opponent_name']} (#{loser_rank})"

        # --- Report Generation ---
        report = {
            "week": week,
            "alternative_universe_winners": alternative_universe_winners,
            "top_points": top_points_team,
            "highest_scoring_loss": highest_scoring_loss,
            "smallest_margin_of_defeat": smallest_margin_team,
            "lowest_scoring_win": lowest_scoring_win,
            "blowout_of_the_week": blowout if blowout['margin'] > 0 else None,
            "giant_killer": giant_killer if giant_killer['rank_diff'] > 0 else None,
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
    season_stats = {name: defaultdict(int) for name in team_names}

    for report in all_weekly_reports:
        # Tally Alternative Universe Wins
        for winner_name in report['alternative_universe_winners']:
            season_stats[winner_name]['alternative_universe_wins'] += 1
        
        # Tally Accolades
        if report.get('top_points'):
            season_stats[report['top_points']['name']]['top_points_weeks'] += 1
        if report.get('highest_scoring_loss'):
            season_stats[report['highest_scoring_loss']['name']]['highest_scoring_loss_weeks'] += 1
        if report.get('smallest_margin_of_defeat'):
            season_stats[report['smallest_margin_of_defeat']['name']]['smallest_margin_defeat_weeks'] += 1
        if report.get('lowest_scoring_win'):
            season_stats[report['lowest_scoring_win']['name']]['lowest_scoring_win_weeks'] += 1

    # The Rollercoaster Award
    team_scores = {name: [] for name in team_names}
    for report in all_weekly_reports:
        for score_data in report['all_scores']:
            team_scores[score_data['name']].append(score_data['score'])
    
    volatility = []
    for name, scores in team_scores.items():
        if len(scores) > 1:
            stdev = statistics.stdev(scores)
            volatility.append({'team': name, 'stdev': round(stdev, 2)})

    # Format the final report for printing
    summary = {
        "Alternative Universe Standings": sorted(
            [{'team': name, 'wins': stats['alternative_universe_wins']} for name, stats in season_stats.items()],
            key=lambda x: x['wins'], reverse=True
        ),
        "Accolade Leaderboard": {
            "The Rollercoaster Award (Most Volatile)": sorted(
                volatility, key=lambda x: x['stdev'], reverse=True
            ),
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

def format_summary_as_markdown(summary):
    """
    Takes the season summary dictionary and formats it into a
    human-readable Markdown string.
    """
    lines = ["# 🏈 Y2K Fantasy Football Season Report 🏈"]

    lines.append("\n## 🌌 Alternative Universe Standings")
    lines.append("---")
    for i, team in enumerate(summary['Alternative Universe Standings']):
        lines.append(f"**{i+1}. {team['team']}**: {team['wins']} wins")

    lines.append("\n## 🏆 Accolade Leaderboard")
    lines.append("---")
    for award_name, leaderboard in summary['Accolade Leaderboard'].items():
        lines.append(f"\n### {award_name}")
        if not leaderboard:
            lines.append("- *No qualifying teams*")
            continue
        # Show the top 3 for each award
        for i, entry in enumerate(leaderboard[:3]):
            emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            value = entry.get('count', entry.get('stdev', 'N/A'))
            lines.append(f"{emoji} **{entry['team']}**: {value}")
            
    return "\n".join(lines)

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
    for week in range(1, end_week + 1):
        print(f"Processing Week {week}...")
        standings = query.get_league_standings()
        weekly_report = process_week(query, week, standings)
        if weekly_report:
            all_weekly_reports.append(weekly_report)
    
    print("\nAll weeks processed. Calculating season summary...")
    season_summary = calculate_season_summary(all_weekly_reports, team_names)
    
    # NEW: Format the summary into a beautiful Markdown report
    markdown_report = format_summary_as_markdown(season_summary)
    
    print("\n" + "="*50)
    print(markdown_report)
    print("="*50)
    
    # You can still save the raw JSON data for archival purposes
    with open("season_summary_data.json", "w") as f:
        json.dump(season_summary, f, indent=4)
    print("\nFull season data saved to season_summary_data.json")

if __name__ == "__main__":
    main()
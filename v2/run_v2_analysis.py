"""
Main entry point for running the v2 analysis and displaying the results.
"""
import sys
sys.path.append(".")

import random
from v2.initialize_league import initialize_league
from v2.models.league import Matchup, Team
from v2.leaderboard import calculate_leaderboards
from v2.display import display_leaderboard

def generate_random_matchups(league):
    """Generates a pseudo-random schedule for the league."""
    teams = league.teams

    # Regular Season
    for week in range(1, league.playoff_settings.start_week):
        league.schedule.regular_season[week] = []
        # Naive matchup generation: just pair teams sequentially
        for i in range(0, len(teams), 2):
            team1 = teams[i]
            team2 = teams[i+1]
            matchup = Matchup(
                week=week,
                team1=team1,
                team2=team2,
                team1_score=round(random.uniform(80, 150), 2),
                team2_score=round(random.uniform(80, 150), 2)
            )
            league.schedule.regular_season[week].append(matchup)

    # Playoffs (simplified)
    playoff_teams = teams[:league.playoff_settings.num_teams]
    for week in range(league.playoff_settings.start_week, 18):
        league.schedule.playoffs[week] = []
        for i in range(0, len(playoff_teams), 2):
            team1 = playoff_teams[i]
            team2 = playoff_teams[i+1]
            matchup = Matchup(
                week=week,
                team1=team1,
                team2=team2,
                team1_score=round(random.uniform(90, 160), 2),
                team2_score=round(random.uniform(90, 160), 2)
            )
            league.schedule.playoffs[week].append(matchup)


def main():
    """
    Initializes the league, runs the analysis, and displays the results.
    """
    print("--- Initializing v2 League Analysis ---")

    # 1. Initialize a sample league
    league = initialize_league()

    # 2. Generate some random matchup data for demonstration
    generate_random_matchups(league)

    # 3. Calculate leaderboards, H2H records, and accolades
    leaderboard_data = calculate_leaderboards(league)

    # 4. Display the results
    display_leaderboard(leaderboard_data)

    print("--- v2 League Analysis Complete ---")

if __name__ == "__main__":
    main()

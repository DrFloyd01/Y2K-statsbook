
from typing import List, Dict

from collections import defaultdict
import statistics

def calculate_leaderboards(matchups: List[Dict], teams: List[Dict]) -> Dict:
    """
    Calculates the standard and alternate universe leaderboards, as well as all the v1 accolades.
    """
    leaderboard = defaultdict(lambda: {
        "wins": 0,
        "losses": 0,
        "points_for": 0,
        "points_against": 0,
        "win_percentage": 0.0,
        "alt_universe_wins": 0,
        "alt_universe_losses": 0
    })

    for team in teams:
        leaderboard[team["team_id"]]["manager_name"] = team["manager_name"]

    for matchup in matchups:
        team1_id = matchup["team1_id"]
        team2_id = matchup["team2_id"]
        team1_score = matchup["team1_score"]
        team2_score = matchup["team2_score"]
        winner_team_id = matchup["winner_team_id"]

        leaderboard[team1_id]["points_for"] += team1_score
        leaderboard[team1_id]["points_against"] += team2_score
        leaderboard[team2_id]["points_for"] += team2_score
        leaderboard[team2_id]["points_against"] += team1_score

        if winner_team_id == team1_id:
            leaderboard[team1_id]["wins"] += 1
            leaderboard[team2_id]["losses"] += 1
        else:
            leaderboard[team2_id]["wins"] += 1
            leaderboard[team1_id]["losses"] += 1

    # Calculate win percentage
    for team_id, stats in leaderboard.items():
        total_games = stats["wins"] + stats["losses"]
        if total_games > 0:
            stats["win_percentage"] = stats["wins"] / total_games

    # --- Accolade & Alt Universe Calculations ---
    weekly_scores = []
    for matchup in matchups:
        weekly_scores.append({"team_id": matchup["team1_id"], "score": matchup["team1_score"]})
        weekly_scores.append({"team_id": matchup["team2_id"], "score": matchup["team2_score"]})

    weekly_scores.sort(key=lambda x: x["score"], reverse=True)
    num_teams = len(weekly_scores)
    median_index = num_teams // 2

    for i, team_score in enumerate(weekly_scores):
        if i < median_index:
            leaderboard[team_score["team_id"]]["alt_universe_wins"] += 1
        else:
            leaderboard[team_score["team_id"]]["alt_universe_losses"] += 1

    # --- Accolades ---
    accolades = {}
    top_team = weekly_scores[0]
    accolades["top_points"] = {
        "team_id": top_team["team_id"],
        "score": top_team["score"]
    }

    losing_teams = []
    for matchup in matchups:
        if matchup["winner_team_id"] == matchup["team1_id"]:
            losing_teams.append({"team_id": matchup["team2_id"], "score": matchup["team2_score"]})
        else:
            losing_teams.append({"team_id": matchup["team1_id"], "score": matchup["team1_score"]})

    if losing_teams:
        highest_scoring_loser = max(losing_teams, key=lambda x: x["score"])
        accolades["highest_scoring_loss"] = {
            "team_id": highest_scoring_loser["team_id"],
            "score": highest_scoring_loser["score"]
        }

    winning_teams = []
    for matchup in matchups:
        if matchup["winner_team_id"] == matchup["team1_id"]:
            winning_teams.append({"team_id": matchup["team1_id"], "score": matchup["team1_score"]})
        else:
            winning_teams.append({"team_id": matchup["team2_id"], "score": matchup["team2_score"]})

    if winning_teams:
        lowest_scoring_winner = min(winning_teams, key=lambda x: x["score"])
        accolades["lowest_scoring_win"] = {
            "team_id": lowest_scoring_winner["team_id"],
            "score": lowest_scoring_winner["score"]
        }

    min_margin, smd_details = float('inf'), None
    for matchup in matchups:
        margin = abs(matchup["team1_score"] - matchup["team2_score"])
        if margin < min_margin:
            min_margin = margin
            loser_id = matchup["team1_id"] if matchup["winner_team_id"] == matchup["team2_id"] else matchup["team2_id"]
            smd_details = {
                "team_id": loser_id,
                "margin": margin
            }
    if smd_details:
        accolades["smallest_margin_defeat"] = smd_details

    max_margin, blowout_details = 0, None
    for matchup in matchups:
        margin = abs(matchup["team1_score"] - matchup["team2_score"])
        if margin > max_margin:
            max_margin = margin
            winner_id = matchup["winner_team_id"]
            blowout_details = {
                "team_id": winner_id,
                "margin": margin
            }
    if blowout_details:
        accolades["blowout_win"] = blowout_details

    return {
        "leaderboard": dict(leaderboard),
        "accolades": accolades
    }


from typing import Dict
from collections import defaultdict
from dataclasses import asdict

from v2.models.league import League, Matchup
from v2.parsers.h2h_parser import parse_h2h_data
from v2.parsers.accolade_parser import parse_accolades

def calculate_leaderboards(league: League, doh_accolades) -> Dict:
    """
    Calculates the standard leaderboards, H2H records, and accolades.
    """
    # --- Standard Leaderboard ---
    leaderboard = defaultdict(lambda: {
        "wins": 0,
        "losses": 0,
        "points_for": 0,
        "points_against": 0,
        "win_percentage": 0.0,
    })

    for team in league.teams:
        leaderboard[team.team_id]["manager_name"] = team.manager_name

    all_matchups = []
    if league.schedule.regular_season:
        for week in league.schedule.regular_season:
            all_matchups.extend(league.schedule.regular_season[week])
    if league.schedule.playoffs:
        for week in league.schedule.playoffs:
            all_matchups.extend(league.schedule.playoffs[week])

    for matchup in all_matchups:
        team1 = matchup.team1
        team2 = matchup.team2
        team1_score = matchup.team1_score
        team2_score = matchup.team2_score

        leaderboard[team1.team_id]["points_for"] += team1_score
        leaderboard[team1.team_id]["points_against"] += team2_score
        leaderboard[team2.team_id]["points_for"] += team2_score
        leaderboard[team2.team_id]["points_against"] += team1_score

        if team1_score > team2_score:
            leaderboard[team1.team_id]["wins"] += 1
            leaderboard[team2.team_id]["losses"] += 1
        else:
            leaderboard[team2.team_id]["wins"] += 1
            leaderboard[team1.team_id]["losses"] += 1

    # Calculate win percentage
    for team_id, stats in leaderboard.items():
        total_games = stats["wins"] + stats["losses"]
        if total_games > 0:
            stats["win_percentage"] = stats["wins"] / total_games

    # --- Alt Universe Accolades ---
    from v2.accolades import calculate_alt_universe_accolades
    alt_universe_accolades = calculate_alt_universe_accolades(league)
    for team in league.teams:
        leaderboard[team.team_id]["alt_universe_wins"] = 0
        leaderboard[team.team_id]["alt_universe_losses"] = 0

    for accolade in alt_universe_accolades:
        for team in league.teams:
            if team.manager_name == accolade["manager"]:
                if accolade["accolade"] == "alt_universe_win":
                    leaderboard[team.team_id]["alt_universe_wins"] += 1
                else:
                    leaderboard[team.team_id]["alt_universe_losses"] += 1


    # --- H2H Records ---
    h2h_records = parse_h2h_data(league)


    # --- Accolades ---
    accolades = parse_accolades(league)

    # --- D'OH Accolades ---
    # Sort accolades by the potential point swing for display
    sorted_doh_accolades = sorted(doh_accolades, key=lambda item: item["point_swing"], reverse=True)

    return {
        "leaderboard": dict(leaderboard),
        "h2h_records": [asdict(record) for record in h2h_records],
        "accolades": [asdict(accolade) for accolade in accolades],
        "doh_accolades": sorted_doh_accolades,
    }

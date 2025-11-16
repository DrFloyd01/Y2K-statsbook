"""
This module contains the logic for calculating league accolades.
"""
from v2.models.league import League, Matchup, Player


def _is_valid_substitution(bench_player: Player, starter: Player) -> bool:
    """
    Checks if a bench player can be substituted for a starter based on position.
    """
    valid_flex_positions = {"WR", "RB", "TE"}

    # QB for QB
    if bench_player.position == "QB" and starter.position == "QB":
        return True
    # K for K
    if bench_player.position == "K" and starter.position == "K":
        return True
    # DEF for DEF
    if bench_player.position == "DEF" and starter.position == "DEF":
        return True
    # WR/RB/TE for WR/RB/TE or FLEX (W/R/T)
    if bench_player.position in valid_flex_positions and (starter.position in valid_flex_positions or starter.position == "W/R/T"):
        return True
    return False


def calculate_doh_accolades(league: League):
    """
    Identifies and calculates 'D'OH' accolades for a given league.

    A 'D'OH' accolade is awarded to a losing team if a single bench player
    substitution could have resulted in a win.
    """
    doh_accolades = []
    for week, matchups in league.schedule.regular_season.items():
        for matchup in matchups:
            # Determine the losing team
            if matchup.team1_score < matchup.team2_score:
                losing_team = matchup.team1
                winning_team = matchup.team2
                losing_score = matchup.team1_score
                winning_score = matchup.team2_score
            else:
                losing_team = matchup.team2
                winning_team = matchup.team1
                losing_score = matchup.team2_score
                winning_score = matchup.team1_score

            losing_margin = winning_score - losing_score

            # Get the starters and bench players for the losing team
            starters = [p for p in losing_team.roster if p.starting_status]
            bench_players = [p for p in losing_team.roster if not p.starting_status]

            # Check for 'D'OH' scenarios
            for bench_player in bench_players:
                for starter in starters:
                    if _is_valid_substitution(bench_player, starter):
                        score_difference = bench_player.actual_score - starter.actual_score
                        if score_difference > losing_margin:
                            doh_accolades.append({
                                "week": week,
                                "losing_team": losing_team.manager_name,
                                "winning_team": winning_team.manager_name,
                                "losing_score": losing_score,
                                "winning_score": winning_score,
                                "margin": losing_margin,
                                "bench_player": bench_player.name,
                                "bench_player_score": bench_player.actual_score,
                                "starting_player": starter.name,
                                "starting_player_score": starter.actual_score,
                                "point_swing": score_difference,
                                "new_score": losing_score + score_difference
                            })

    # Sort accolades by week, then by losing team, then by point swing descending
    doh_accolades.sort(key=lambda x: (x["week"], x["losing_team"], -x["point_swing"]))

    return doh_accolades


def calculate_alt_universe_accolades(league: League):
    """
    Calculates the 'Alternative Universe' accolades for a given league.

    An 'Alternative Universe' win is awarded to a team if they score in the
    top half of the league for a given week.
    """
    alt_universe_accolades = []
    for week, matchups in league.schedule.regular_season.items():
        weekly_scores = []
        for matchup in matchups:
            weekly_scores.append({"manager": matchup.team1.manager_name, "score": matchup.team1_score})
            weekly_scores.append({"manager": matchup.team2.manager_name, "score": matchup.team2_score})

        weekly_scores.sort(key=lambda x: x['score'], reverse=True)
        num_teams = len(weekly_scores)
        median_index = num_teams // 2

        for team in weekly_scores[:median_index]:
            alt_universe_accolades.append({
                "week": week,
                "manager": team["manager"],
                "accolade": "alt_universe_win"
            })
        for team in weekly_scores[median_index:]:
            alt_universe_accolades.append({
                "week": week,
                "manager": team["manager"],
                "accolade": "alt_universe_loss"
            })

    return alt_universe_accolades

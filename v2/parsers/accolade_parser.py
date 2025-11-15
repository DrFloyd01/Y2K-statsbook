"""
Parses weekly accolades from league data.
"""
from typing import List
from v2.models.league import League, Accolade, Matchup

def parse_accolades(league: League) -> List[Accolade]:
    """
    Parses all weekly matchups and returns a list of Accolade objects.
    """
    accolades: List[Accolade] = []
    all_matchups_by_week = {**league.schedule.regular_season, **league.schedule.playoffs}

    for week, matchups in all_matchups_by_week.items():
        if not matchups:
            continue

        # --- Top Points ---
        all_teams_scores = []
        for m in matchups:
            all_teams_scores.append({"team": m.team1, "score": m.team1_score, "opponent": m.team2})
            all_teams_scores.append({"team": m.team2, "score": m.team2_score, "opponent": m.team1})

        top_performer = max(all_teams_scores, key=lambda x: x["score"])
        accolades.append(Accolade(
            name="Top Points",
            manager_name=top_performer["team"].manager_name,
            week=week,
            season=league.season,
            magnitude=top_performer["score"],
            opponent_manager_name=top_performer["opponent"].manager_name
        ))

        # --- Winners and Losers ---
        winners = []
        losers = []
        for m in matchups:
            if m.team1_score > m.team2_score:
                winners.append({"team": m.team1, "score": m.team1_score, "opponent": m.team2})
                losers.append({"team": m.team2, "score": m.team2_score, "opponent": m.team1})
            else:
                winners.append({"team": m.team2, "score": m.team2_score, "opponent": m.team1})
                losers.append({"team": m.team1, "score": m.team1_score, "opponent": m.team2})

        # --- Highest Scoring Loss ---
        if losers:
            highest_scoring_loser = max(losers, key=lambda x: x["score"])
            accolades.append(Accolade(
                name="Highest Scoring Loss",
                manager_name=highest_scoring_loser["team"].manager_name,
                week=week,
                season=league.season,
                magnitude=highest_scoring_loser["score"],
                opponent_manager_name=highest_scoring_loser["opponent"].manager_name
            ))

        # --- Lowest Scoring Win ---
        if winners:
            lowest_scoring_winner = min(winners, key=lambda x: x["score"])
            accolades.append(Accolade(
                name="Lowest Scoring Win",
                manager_name=lowest_scoring_winner["team"].manager_name,
                week=week,
                season=league.season,
                magnitude=lowest_scoring_winner["score"],
                opponent_manager_name=lowest_scoring_winner["opponent"].manager_name
            ))

        # --- Margins ---
        margins = []
        for m in matchups:
            margin = abs(m.team1_score - m.team2_score)
            if m.team1_score > m.team2_score:
                winner, loser = m.team1, m.team2
            else:
                winner, loser = m.team2, m.team1
            margins.append({"margin": margin, "winner": winner, "loser": loser})

        # --- Smallest Margin Defeat ---
        if margins:
            smallest_margin = min(margins, key=lambda x: x["margin"])
            accolades.append(Accolade(
                name="Smallest Margin Defeat",
                manager_name=smallest_margin["loser"].manager_name,
                week=week,
                season=league.season,
                magnitude=smallest_margin["margin"],
                opponent_manager_name=smallest_margin["winner"].manager_name
            ))

        # --- Blowout of the Week ---
        if margins:
            largest_margin = max(margins, key=lambda x: x["margin"])
            accolades.append(Accolade(
                name="Blowout of the Week",
                manager_name=largest_margin["winner"].manager_name,
                week=week,
                season=league.season,
                magnitude=largest_margin["margin"],
                opponent_manager_name=largest_margin["loser"].manager_name
            ))

    return accolades

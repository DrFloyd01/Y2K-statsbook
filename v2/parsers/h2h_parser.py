"""
Parses head-to-head records from league data.
"""
from typing import List, Dict
from v2.models.league import League, H2HRecord, Matchup, Team

def parse_h2h_data(league: League) -> List[H2HRecord]:
    """
    Parses matchup data and returns a list of H2HRecord objects.
    """
    # Use a dictionary for easier lookup, with a tuple of sorted manager names as key
    h2h_records: Dict[tuple[str, str], H2HRecord] = {}

    all_matchups: List[Matchup] = []

    # Combine regular season and playoff matchups
    if league.schedule.regular_season:
        for week in sorted(league.schedule.regular_season.keys()):
            all_matchups.extend(league.schedule.regular_season[week])

    if league.schedule.playoffs:
        for week in sorted(league.schedule.playoffs.keys()):
            all_matchups.extend(league.schedule.playoffs[week])

    for matchup in all_matchups:
        team1: Team = matchup.team1
        team2: Team = matchup.team2

        manager1_name = team1.manager_name
        manager2_name = team2.manager_name

        # Create a consistent key for the manager pair
        key = tuple(sorted((manager1_name, manager2_name)))

        if key not in h2h_records:
            # key[0] is manager_name, key[1] is opponent_name.
            h2h_records[key] = H2HRecord(
                manager_name=key[0],
                opponent_name=key[1]
            )

        record = h2h_records[key]

        is_playoff = league.playoff_settings and matchup.week >= league.playoff_settings.start_week

        if matchup.team1_score > matchup.team2_score:
            winner_name = manager1_name
        else:
            winner_name = manager2_name

        # Update wins/losses
        if winner_name == record.manager_name:
            if is_playoff:
                record.playoff_wins += 1
            else:
                record.season_wins += 1
        else: # winner is opponent
            if is_playoff:
                record.playoff_losses += 1
            else:
                record.season_losses += 1

    # TODO: Add streak calculation. This will require modifying the H2HRecord model
    # to store streak information. This will be addressed in a future step.

    return list(h2h_records.values())

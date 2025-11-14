"""
Initialization script to demonstrate the v2 data models.
"""
from v2.models.league import (
    League,
    Team,
    Player,
    RosterSettings,
    ScoringSettings,
    PlayoffSettings,
    Schedule,
    Matchup
)

def initialize_league():
    """
    Creates and configures a new League object with custom settings.
    """
    # 1. Create a new League instance
    my_league = League(
        league_id="123456",
        season=2025,
        name="My Awesome League"
    )

    # 2. Define custom roster settings (e.g., 3 WRs)
    my_league.roster_settings = RosterSettings(
        qb=1,
        rb=2,
        wr=3,
        te=1,
        flex=1,
        k=1,
        dl=1,
        lb=1,
        db=1,
        bench=7
    )

    # 3. Define custom scoring settings (6-point passing TDs, PPR)
    my_league.scoring_settings = ScoringSettings(
        pass_td=6.0,
        pass_yd=0.04,
        rush_yd=0.1,
        rec_yd=0.1,
        rec=1.0
    )

    # 4. Define custom playoff settings (10-man league, 6-team playoff)
    my_league.playoff_settings = PlayoffSettings(
        num_teams=6,
        num_byes=2,
        start_week=15
    )

    # 5. Create teams and add them to the league
    manager_names = [
        "Manager 1", "Manager 2", "Manager 3", "Manager 4", "Manager 5",
        "Manager 6", "Manager 7", "Manager 8", "Manager 9", "Manager 10"
    ]
    for i, name in enumerate(manager_names):
        team = Team(team_id=str(i + 1), manager_name=name)
        my_league.teams.append(team)

    return my_league

if __name__ == "__main__":
    # Initialize the league
    league = initialize_league()

    # Print out the league configuration to verify
    print("--- League Initialized ---")
    print(f"League Name: {league.name}")
    print(f"Season: {league.season}")
    print(f"Number of Teams: {len(league.teams)}")

    print("\n--- Roster Settings ---")
    print(f"WRs: {league.roster_settings.wr}")
    print(f"Bench Spots: {league.roster_settings.bench}")

    print("\n--- Scoring Settings ---")
    print(f"Passing TD: {league.scoring_settings.pass_td} points")
    print(f"PPR: {league.scoring_settings.rec} points per reception")

    print("\n--- Playoff Settings ---")
    print(f"Playoff Teams: {league.playoff_settings.num_teams}")
    print(f"Playoff Byes: {league.playoff_settings.num_byes}")
    print(f"Playoffs Start Week: {league.playoff_settings.start_week}")

    print("\n--- Teams ---")
    for team in league.teams:
        print(f"- {team.manager_name} (ID: {team.team_id})")

    print("\n--- Pseudo Code Verification Complete ---")

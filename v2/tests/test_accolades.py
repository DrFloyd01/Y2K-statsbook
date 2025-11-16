
import unittest
import sys
from pathlib import Path

sys.path.append(".")
from v2.accolades import calculate_doh_accolades, calculate_alt_universe_accolades
from v2.models.league import League, Team, Player, Matchup, Schedule

class TestAccolades(unittest.TestCase):
    def setUp(self):
        """Set up a mock league object for testing."""
        self.league = League(league_id="123", season=2025, name="Test League")

        # Team 1 (Loser)
        team1_roster = [
            Player(player_id=1, name="Starter 1", position="QB", nfl_team="A", starting_status=True, actual_score=10.0),
            Player(player_id=2, name="Bench Player 1", position="QB", nfl_team="A", starting_status=False, actual_score=30.0),
        ]
        self.team1 = Team(team_id=1, manager_name="Manager 1", roster=team1_roster)

        # Team 2 (Winner)
        team2_roster = [
            Player(player_id=3, name="Starter 2", position="QB", nfl_team="B", starting_status=True, actual_score=25.0),
        ]
        self.team2 = Team(team_id=2, manager_name="Manager 2", roster=team2_roster)

        self.league.teams = [self.team1, self.team2]

        # Matchup
        team1_score = sum(p.actual_score for p in team1_roster if p.starting_status)
        team2_score = sum(p.actual_score for p in team2_roster if p.starting_status)
        matchup = Matchup(
            week=1,
            team1=self.team1,
            team2=self.team2,
            team1_score=team1_score,
            team2_score=team2_score,
        )
        self.league.schedule = Schedule(regular_season={1: [matchup]})

    def test_calculate_doh_accolades(self):
        """Test that the 'D'OH' accolade is correctly identified."""
        doh_accolades = calculate_doh_accolades(self.league)
        self.assertEqual(len(doh_accolades), 1)

        doh = doh_accolades[0]
        self.assertEqual(doh["losing_team"], "Manager 1")
        self.assertEqual(doh["winning_team"], "Manager 2")
        self.assertEqual(doh["margin"], 15.0)
        self.assertEqual(doh["bench_player"], "Bench Player 1")
        self.assertEqual(doh["starting_player"], "Starter 1")
        self.assertEqual(doh["point_swing"], 20.0)

    def test_calculate_alt_universe_accolades(self):
        """Test that the 'Alternative Universe' accolade is correctly calculated."""
        alt_universe_accolades = calculate_alt_universe_accolades(self.league)
        self.assertEqual(len(alt_universe_accolades), 2)

        manager1_accolades = [a for a in alt_universe_accolades if a["manager"] == "Manager 1"]
        manager2_accolades = [a for a in alt_universe_accolades if a["manager"] == "Manager 2"]

        self.assertEqual(len(manager1_accolades), 1)
        self.assertEqual(manager1_accolades[0]["accolade"], "alt_universe_loss")

        self.assertEqual(len(manager2_accolades), 1)
        self.assertEqual(manager2_accolades[0]["accolade"], "alt_universe_win")

if __name__ == '__main__':
    unittest.main()

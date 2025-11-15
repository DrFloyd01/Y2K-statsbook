"""
Unit tests for the new v2 features (H2H, accolades, display).
"""
import unittest
import sys
sys.path.append(".")

from v2.models.league import League, Team, Matchup, H2HRecord, Accolade
from v2.parsers.h2h_parser import parse_h2h_data
from v2.parsers.accolade_parser import parse_accolades
from v2.display import display_h2h_records, display_top_5_accolades, display_total_accolades
from v2.initialize_league import initialize_league

class TestNewFeatures(unittest.TestCase):

    def setUp(self):
        """Set up a sample league with matchup data for testing."""
        self.league = initialize_league()

        # Create a simple, predictable schedule
        team1, team2, team3, team4 = self.league.teams[0], self.league.teams[1], self.league.teams[2], self.league.teams[3]

        self.league.schedule.regular_season = {
            1: [
                Matchup(week=1, team1=team1, team2=team2, team1_score=100, team2_score=90),
                Matchup(week=1, team1=team3, team2=team4, team1_score=110, team2_score=120),
            ],
            2: [
                Matchup(week=2, team1=team1, team2=team3, team1_score=95, team2_score=105),
            ]
        }
        self.league.schedule.playoffs = {
            15: [
                Matchup(week=15, team1=team1, team2=team2, team1_score=130, team2_score=110),
            ]
        }

    def test_h2h_parser(self):
        """Test the H2H parser with a simple schedule."""
        h2h_records = parse_h2h_data(self.league)

        # There should be 3 records: (1 vs 2), (3 vs 4), (1 vs 3)
        self.assertEqual(len(h2h_records), 3)

        # Find the record for Manager 1 vs Manager 2
        record_1_vs_2 = next((r for r in h2h_records if "Manager 1" in (r.manager_name, r.opponent_name) and "Manager 2" in (r.manager_name, r.opponent_name)), None)

        self.assertIsNotNone(record_1_vs_2)
        # 1 win in regular season, 1 win in playoffs
        self.assertEqual(record_1_vs_2.season_wins, 1)
        self.assertEqual(record_1_vs_2.playoff_wins, 1)
        self.assertEqual(record_1_vs_2.season_losses, 0)
        self.assertEqual(record_1_vs_2.playoff_losses, 0)

    def test_accolade_parser(self):
        """Test the accolade parser with a simple schedule."""
        accolades = parse_accolades(self.league)

        # Check for "Top Points" in Week 1
        top_points_wk1 = next((a for a in accolades if a.name == "Top Points" and a.week == 1), None)
        self.assertIsNotNone(top_points_wk1)
        self.assertEqual(top_points_wk1.manager_name, "Manager 4")
        self.assertEqual(top_points_wk1.magnitude, 120)

        # Check for "Lowest Scoring Win" in Week 1
        lowest_win_wk1 = next((a for a in accolades if a.name == "Lowest Scoring Win" and a.week == 1), None)
        self.assertIsNotNone(lowest_win_wk1)
        self.assertEqual(lowest_win_wk1.manager_name, "Manager 1")
        self.assertEqual(lowest_win_wk1.magnitude, 100)

    def test_display_functions(self):
        """
        Test that the display functions run without errors.
        This is a simple smoke test, not a test of the output's correctness.
        """
        try:
            h2h_records = parse_h2h_data(self.league)
            accolades = parse_accolades(self.league)

            display_h2h_records(h2h_records)
            display_top_5_accolades(accolades)
            display_total_accolades(accolades, num_seasons=1)
        except Exception as e:
            self.fail(f"Display functions raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()

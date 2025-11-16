
import unittest
import sys
from pathlib import Path

sys.path.append(".")
sys.path.append("v2")
from v2.leaderboard import calculate_leaderboards
from v2.parsers.scoreboard_parser import parse_scoreboard_data
from v2.parsers.league_parser import parse_league_data
from v2.tests.test_accolades import TestAccolades

class TestLeaderboard(unittest.TestCase):

    def test_calculate_leaderboards(self):
        """
        Tests that the leaderboard calculations are correct.
        """
        cache_dir = Path("v2/api_cache")
        year = 2025
        week = 1

        accolades_test = TestAccolades()
        accolades_test.setUp()
        league = accolades_test.league
        from v2.accolades import calculate_doh_accolades
        doh_accolades = calculate_doh_accolades(league)

        result = calculate_leaderboards(league, doh_accolades)

        self.assertIn("leaderboard", result)
        self.assertIn("accolades", result)
        self.assertIn("doh_accolades", result)

        leaderboard = result["leaderboard"]
        self.assertEqual(len(leaderboard), 2)

        team1_stats = leaderboard[1]
        self.assertEqual(team1_stats["wins"], 0)
        self.assertEqual(team1_stats["losses"], 1)
        self.assertAlmostEqual(team1_stats["points_for"], 10.0)
        self.assertAlmostEqual(team1_stats["points_against"], 25.0)
        self.assertAlmostEqual(team1_stats["win_percentage"], 0.0)
        self.assertEqual(team1_stats["alt_universe_wins"], 0)
        self.assertEqual(team1_stats["alt_universe_losses"], 1)

if __name__ == '__main__':
    unittest.main()

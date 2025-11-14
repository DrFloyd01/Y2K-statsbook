
import unittest
import sys
from pathlib import Path

sys.path.append(".")
from v2.leaderboard import calculate_leaderboards
from v2.parsers.scoreboard_parser import parse_scoreboard_data
from v2.parsers.league_parser import parse_league_data

class TestLeaderboard(unittest.TestCase):

    def test_calculate_leaderboards(self):
        """
        Tests that the leaderboard calculations are correct.
        """
        cache_dir = Path("v2/api_cache")
        year = 2025
        week = 1

        matchups = parse_scoreboard_data(cache_dir, year, week)
        league = parse_league_data(cache_dir, year, week)
        teams = [{"team_id": team.team_id, "manager_name": team.manager_name} for team in league.teams]

        result = calculate_leaderboards(matchups, teams)

        self.assertIn("leaderboard", result)
        self.assertIn("accolades", result)

        leaderboard = result["leaderboard"]
        self.assertEqual(len(leaderboard), 10)

        team1_stats = leaderboard[1]
        self.assertEqual(team1_stats["wins"], 1)
        self.assertEqual(team1_stats["losses"], 0)
        self.assertAlmostEqual(team1_stats["points_for"], 150.1)
        self.assertAlmostEqual(team1_stats["points_against"], 103.26)
        self.assertAlmostEqual(team1_stats["win_percentage"], 1.0)
        self.assertEqual(team1_stats["alt_universe_wins"], 1)
        self.assertEqual(team1_stats["alt_universe_losses"], 0)

if __name__ == '__main__':
    unittest.main()

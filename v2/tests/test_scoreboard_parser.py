
import unittest
import sys
from pathlib import Path

sys.path.append(".")
from v2.parsers.scoreboard_parser import parse_scoreboard_data

class TestScoreboardParser(unittest.TestCase):

    def test_parse_scoreboard_data(self):
        """
        Tests that the scoreboard parser correctly transforms raw data into a list of matchups.
        """
        cache_dir = Path("v2/api_cache")
        year = 2025
        week = 1

        matchups = parse_scoreboard_data(cache_dir, year, week)

        self.assertIsInstance(matchups, list)
        self.assertEqual(len(matchups), 5)

        matchup = matchups[0]
        self.assertIsInstance(matchup, dict)
        self.assertIn("week", matchup)
        self.assertIn("team1_id", matchup)
        self.assertIn("team1_score", matchup)
        self.assertIn("team2_id", matchup)
        self.assertIn("team2_score", matchup)
        self.assertIn("winner_team_id", matchup)

if __name__ == '__main__':
    unittest.main()


import unittest
import sys
from pathlib import Path

sys.path.append(".")
sys.path.append("v2")
from v2.parsers.league_parser import parse_league_data, parse_weekly_rosters
from v2.models.league import League, Team, Player

class TestLeagueParser(unittest.TestCase):

    def test_parse_league_data(self):
        """
        Tests that the league parser correctly transforms raw data into a League object.
        """
        cache_dir = Path("v2/api_cache")
        year = 2025
        week = 1

        from v2.parsers.main_parser import load_league_from_cache
        league = load_league_from_cache(cache_dir, year)

        self.assertIsInstance(league, League)
        self.assertEqual(league.league_id, "97974")
        self.assertEqual(league.name, "Y2K CPU Machinations")
        self.assertEqual(league.season, 2025)
        self.assertEqual(len(league.teams), 10)

        team = league.teams[0]
        self.assertIsInstance(team, Team)
        self.assertEqual(team.team_id, 1)
        self.assertEqual(team.manager_name, "Dylan")
        self.assertEqual(len(team.roster), 18)

        player = team.roster[0]
        self.assertIsInstance(player, Player)
        self.assertEqual(player.player_id, 30977)
        self.assertEqual(player.name, "Josh Allen")
        self.assertEqual(player.position, "QB")
        self.assertEqual(player.nfl_team, "Buf")

    def test_parse_weekly_rosters(self):
        """
        Tests that the weekly roster parser correctly updates the league object.
        """
        cache_dir = Path("v2/api_cache")
        year = 2025
        week = 2

        from v2.parsers.main_parser import load_league_from_cache
        league = load_league_from_cache(cache_dir, year)
        parse_weekly_rosters(league, cache_dir, year, week)

        # check that dylan's roster is correct for week 2
        dylan = league.get_team_by_id(1)
        self.assertEqual(dylan.roster[0].name, "Josh Allen")
        self.assertEqual(dylan.roster[0].actual_score, 12.32)
        self.assertEqual(dylan.roster[0].starting_status, True)


if __name__ == '__main__':
    unittest.main()

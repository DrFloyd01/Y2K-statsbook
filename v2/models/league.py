"""
Core data models for the v2 fantasy football league.
"""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Player:
    """Represents a real-life NFL player."""
    player_id: str
    name: str
    position: str
    nfl_team: str
    starting_status: bool  # True if in starting lineup, False if on bench
    actual_score: float

@dataclass
class Team:
    """Represents a fantasy team in the league."""
    team_id: str
    manager_name: str
    roster: List[Player] = field(default_factory=list)

@dataclass
class RosterSettings:
    """Defines the structure of a fantasy roster."""
    qb: int = 1
    rb: int = 2
    wr: int = 3
    te: int = 1
    flex: int = 1
    k: int = 1
    dl: int = 1
    lb: int = 1
    db: int = 1
    bench: int = 7

@dataclass
class ScoringSettings:
    """Defines the scoring rules for the league."""
    pass_td: float = 6.0
    pass_yd: float = 0.04
    rush_yd: float = 0.1
    rec_yd: float = 0.1
    rec: float = 1.0
    # Add other scoring rules as needed

@dataclass
class PlayoffSettings:
    """Defines the structure of the playoffs."""
    num_teams: int = 6
    num_byes: int = 2
    start_week: int = 15

@dataclass
class Matchup:
    """Represents a head-to-head matchup between two teams."""
    week: int
    team1: Team
    team2: Team
    team1_score: float = 0.0
    team2_score: float = 0.0

@dataclass
class Schedule:
    """Holds the schedule for the entire season."""
    regular_season: Dict[int, List[Matchup]] = field(default_factory=dict)
    playoffs: Dict[int, List[Matchup]] = field(default_factory=dict)

@dataclass
class H2HRecord:
    """Represents a head-to-head record between two managers."""
    manager_name: str
    opponent_name: str
    season_wins: int = 0
    season_losses: int = 0
    playoff_wins: int = 0
    playoff_losses: int = 0


@dataclass
class Accolade:
    """Represents a single accolade instance."""
    name: str
    manager_name: str
    week: int
    season: int
    magnitude: float
    opponent_manager_name: str = ""


@dataclass
class League:
    """The main container class for all league data."""
    league_id: str
    season: int
    name: str
    teams: List[Team] = field(default_factory=list)
    roster_settings: RosterSettings = field(default_factory=RosterSettings)
    scoring_settings: ScoringSettings = field(default_factory=ScoringSettings)
    playoff_settings: PlayoffSettings = field(default_factory=PlayoffSettings)
    schedule: Schedule = field(default_factory=Schedule)
    h2h_records: List[H2HRecord] = field(default_factory=list)
    accolades: List[Accolade] = field(default_factory=list)

    def get_team_by_id(self, team_id: int) -> Team | None:
        """
        Returns a team from the league by its ID.
        """
        for team in self.teams:
            if team.team_id == team_id:
                return team
        return None

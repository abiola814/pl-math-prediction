"""Corner statistics aggregator — NEW (no pldashboard equivalent).

Uses API-Football fixture statistics to compute per-team corner averages.
"""

from dataclasses import dataclass

from app.models.fixture import Fixture
from app.models.fixture_stats import FixtureStatistics


@dataclass
class CornerProfile:
    avg_corners_for_home: float
    avg_corners_for_away: float
    avg_corners_against_home: float
    avg_corners_against_away: float
    total_matches: int

    @property
    def avg_corners_for(self) -> float:
        return (self.avg_corners_for_home + self.avg_corners_for_away) / 2

    @property
    def avg_corners_against(self) -> float:
        return (self.avg_corners_against_home + self.avg_corners_against_away) / 2


class CornerStatsCalculator:
    def compute_corner_profile(
        self,
        team_api_id: int,
        team_name: str,
        fixtures: list[Fixture],
        all_stats: list[FixtureStatistics],
    ) -> CornerProfile:
        """Build a corner profile for a team from historical data.

        Args:
            team_api_id: API-Football team ID
            team_name: Team name (to determine home/away)
            fixtures: Finished fixtures involving this team
            all_stats: All FixtureStatistics rows for this team
        """
        # Index stats by fixture_api_id for fast lookup
        stats_by_fixture: dict[int, FixtureStatistics] = {}
        for s in all_stats:
            if s.team_api_id == team_api_id and s.corners is not None:
                stats_by_fixture[s.fixture_api_id] = s

        # Also need opponent stats — collect all stats indexed by (fixture_id, team_id)
        opponent_stats: dict[int, list[FixtureStatistics]] = {}
        for s in all_stats:
            if s.team_api_id != team_api_id and s.corners is not None:
                opponent_stats.setdefault(s.fixture_api_id, []).append(s)

        home_corners_for: list[int] = []
        away_corners_for: list[int] = []
        home_corners_against: list[int] = []
        away_corners_against: list[int] = []

        for fix in fixtures:
            if fix.api_id not in stats_by_fixture:
                continue
            team_stat = stats_by_fixture[fix.api_id]
            opp_list = opponent_stats.get(fix.api_id, [])
            opp_corners = opp_list[0].corners if opp_list else 0

            is_home = fix.home_team_name == team_name
            if is_home:
                home_corners_for.append(team_stat.corners)
                home_corners_against.append(opp_corners)
            else:
                away_corners_for.append(team_stat.corners)
                away_corners_against.append(opp_corners)

        def avg(lst: list[int]) -> float:
            return sum(lst) / len(lst) if lst else 5.0  # Default ~5 corners

        return CornerProfile(
            avg_corners_for_home=avg(home_corners_for),
            avg_corners_for_away=avg(away_corners_for),
            avg_corners_against_home=avg(home_corners_against),
            avg_corners_against_away=avg(away_corners_against),
            total_matches=len(home_corners_for) + len(away_corners_for),
        )

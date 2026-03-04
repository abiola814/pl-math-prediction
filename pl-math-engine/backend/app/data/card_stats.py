"""Card statistics aggregator — computes per-team yellow card averages.

Uses API-Football fixture statistics to compute per-team card averages
(home/away splits), following the same pattern as corner_stats.py.
"""

from dataclasses import dataclass

from app.models.fixture import Fixture
from app.models.fixture_stats import FixtureStatistics


@dataclass
class CardProfile:
    avg_yellows_for_home: float
    avg_yellows_for_away: float
    avg_yellows_against_home: float
    avg_yellows_against_away: float
    total_matches: int

    @property
    def avg_yellows_for(self) -> float:
        return (self.avg_yellows_for_home + self.avg_yellows_for_away) / 2

    @property
    def avg_yellows_against(self) -> float:
        return (self.avg_yellows_against_home + self.avg_yellows_against_away) / 2


class CardStatsCalculator:
    def compute_card_profile(
        self,
        team_api_id: int,
        team_name: str,
        fixtures: list[Fixture],
        all_stats: list[FixtureStatistics],
    ) -> CardProfile:
        """Build a yellow card profile for a team from historical data.

        Args:
            team_api_id: API-Football team ID
            team_name: Team name (to determine home/away)
            fixtures: Finished fixtures involving this team
            all_stats: All FixtureStatistics rows for this team
        """
        # Index stats by fixture_api_id for fast lookup
        stats_by_fixture: dict[int, FixtureStatistics] = {}
        for s in all_stats:
            if s.team_api_id == team_api_id and s.yellow_cards is not None:
                stats_by_fixture[s.fixture_api_id] = s

        # Also need opponent stats
        opponent_stats: dict[int, list[FixtureStatistics]] = {}
        for s in all_stats:
            if s.team_api_id != team_api_id and s.yellow_cards is not None:
                opponent_stats.setdefault(s.fixture_api_id, []).append(s)

        home_yellows_for: list[int] = []
        away_yellows_for: list[int] = []
        home_yellows_against: list[int] = []
        away_yellows_against: list[int] = []

        for fix in fixtures:
            if fix.api_id not in stats_by_fixture:
                continue
            team_stat = stats_by_fixture[fix.api_id]
            opp_list = opponent_stats.get(fix.api_id, [])
            opp_yellows = opp_list[0].yellow_cards if opp_list else 0

            is_home = fix.home_team_name == team_name
            if is_home:
                home_yellows_for.append(team_stat.yellow_cards)
                home_yellows_against.append(opp_yellows)
            else:
                away_yellows_for.append(team_stat.yellow_cards)
                away_yellows_against.append(opp_yellows)

        def avg(lst: list[int]) -> float:
            return sum(lst) / len(lst) if lst else 2.0  # Default ~2 yellows/match

        return CardProfile(
            avg_yellows_for_home=avg(home_yellows_for),
            avg_yellows_for_away=avg(away_yellows_for),
            avg_yellows_against_home=avg(home_yellows_against),
            avg_yellows_against_away=avg(away_yellows_against),
            total_matches=len(home_yellows_for) + len(away_yellows_for),
        )

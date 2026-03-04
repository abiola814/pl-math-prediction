"""Home advantage calculator — ported from pldashboard HomeAdvantages.

Algorithm:
  home_advantage = home_win_ratio - overall_win_ratio
  Averaged across seasons, excluding COVID 2020
"""

from app.config import settings
from app.models.fixture import Fixture


class HomeAdvantageCalculator:
    PANDEMIC_YEAR = settings.PANDEMIC_YEAR  # 2020

    def compute(
        self,
        fixtures_by_season: dict[int, list[Fixture]],
        current_season: int,
        home_games_threshold: int = settings.HOME_GAMES_THRESHOLD,
    ) -> dict[str, float]:
        """Compute home advantage for every team in the current season.

        Returns: {team_name: home_advantage_value}
        """
        # Collect per-team, per-season stats
        # {team_name: {season: {home_wins, home_played, total_wins, total_played}}}
        stats: dict[str, dict[int, dict[str, int]]] = {}

        for season, fixtures in fixtures_by_season.items():
            for fix in fixtures:
                if fix.home_goals is None or fix.away_goals is None:
                    continue

                home = fix.home_team_name
                away = fix.away_team_name

                for team_name in (home, away):
                    stats.setdefault(team_name, {}).setdefault(season, {
                        "home_wins": 0, "home_played": 0,
                        "total_wins": 0, "total_played": 0,
                    })

                home_s = stats[home][season]
                away_s = stats[away][season]

                # Home team played at home
                home_s["home_played"] += 1
                home_s["total_played"] += 1
                # Away team played away
                away_s["total_played"] += 1

                if fix.home_goals > fix.away_goals:
                    home_s["home_wins"] += 1
                    home_s["total_wins"] += 1
                elif fix.away_goals > fix.home_goals:
                    away_s["total_wins"] += 1

        # Get current season teams
        current_teams = set()
        for fix in fixtures_by_season.get(current_season, []):
            current_teams.add(fix.home_team_name)
            current_teams.add(fix.away_team_name)

        # Compute average home advantage across seasons
        result: dict[str, float] = {}
        for team in current_teams:
            season_advantages: list[float] = []
            for season, s in stats.get(team, {}).items():
                # Skip pandemic year
                if season == self.PANDEMIC_YEAR:
                    continue
                # Skip current season if not enough home games
                if season == current_season and s["home_played"] <= home_games_threshold:
                    continue
                if s["home_played"] == 0 or s["total_played"] == 0:
                    continue

                home_win_ratio = s["home_wins"] / s["home_played"]
                overall_win_ratio = s["total_wins"] / s["total_played"]
                season_advantages.append(home_win_ratio - overall_win_ratio)

            result[team] = (
                sum(season_advantages) / len(season_advantages)
                if season_advantages
                else 0.0
            )

        return result

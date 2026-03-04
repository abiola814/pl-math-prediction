"""Team strength ratings — ported from pldashboard TeamRatings.

Algorithm:
  rating = points + goal_difference
  Normalized to [0, 1] per season
  Exponentially weighted across seasons (2.5x multiplier per season)
"""

import numpy as np

from app.config import settings
from app.models.standing import Standing


class TeamRatingCalculator:
    MULTIPLIER = settings.SEASON_RATING_MULTIPLIER  # 2.5

    def _get_season_weights(self, num_seasons: int) -> list[float]:
        """Exponential recency weights — most recent season is heaviest.

        From pldashboard team_ratings.py:
          weights = [0.01 * (2.5^3), 0.01 * (2.5^2), 0.01 * 2.5, 0.01]
          normalized to sum to 1.
        Index 0 = current season, index N = N seasons ago.
        """
        weights = np.array([
            0.01 * (self.MULTIPLIER ** (num_seasons - 1 - i))
            for i in range(num_seasons)
        ])
        return list(weights / weights.sum())

    @staticmethod
    def _calc_raw_rating(points: int, gd: int) -> float:
        return float(points + gd)

    def compute(
        self,
        standings_by_season: dict[int, list[Standing]],
        current_season: int,
        games_threshold: int = settings.GAMES_THRESHOLD,
    ) -> dict[str, float]:
        """Compute total team rating for every team in the current season.

        Returns: {team_name: rating} where rating is in [0, 1].
        """
        seasons_sorted = sorted(standings_by_season.keys(), reverse=True)
        num_seasons = len(seasons_sorted)

        # Step 1: Collect raw ratings per team per season
        # {team_name: {season: raw_rating}}
        raw: dict[str, dict[int, float]] = {}
        for season, standings in standings_by_season.items():
            for s in standings:
                raw.setdefault(s.team_name, {})[season] = self._calc_raw_rating(
                    s.points, s.goal_difference
                )

        # Only include teams in the current season
        current_teams = {
            s.team_name for s in standings_by_season.get(current_season, [])
        }

        # Step 2: Normalize per-season ratings to [0, 1]
        for season in seasons_sorted:
            season_values = [
                raw[t][season] for t in current_teams if season in raw.get(t, {})
            ]
            if not season_values:
                continue
            min_val = min(season_values)
            max_val = max(season_values)
            spread = max_val - min_val if max_val != min_val else 1.0
            for team in current_teams:
                if season in raw.get(team, {}):
                    raw[team][season] = (raw[team][season] - min_val) / spread

        # Step 3: Check if current season should be included
        include_current = True
        current_standings = standings_by_season.get(current_season, [])
        if current_standings and all(s.played <= games_threshold for s in current_standings):
            include_current = False

        # Step 4: Compute weighted total
        if include_current:
            active_seasons = seasons_sorted
        else:
            active_seasons = [s for s in seasons_sorted if s != current_season]

        weights = self._get_season_weights(len(active_seasons))

        result: dict[str, float] = {}
        for team in current_teams:
            total = 0.0
            for i, season in enumerate(active_seasons):
                rating = raw.get(team, {}).get(season, 0.0)
                total += weights[i] * rating
            result[team] = total

        return result

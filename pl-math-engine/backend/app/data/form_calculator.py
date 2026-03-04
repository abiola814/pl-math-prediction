"""Team form calculator — ported from pldashboard form.py.

Algorithm:
  form = 0.5 + Σ(opposition_rating × goal_diff × weight)
  Clamped to [0, 1]
  Linear weights from 0.2 to 1.0 over last N matches
"""

import numpy as np

from app.config import settings
from app.models.fixture import Fixture


class FormCalculator:
    def calc_form(
        self,
        team_name: str,
        recent_fixtures: list[Fixture],
        team_ratings: dict[str, float],
        num_matches: int = settings.FORM_MATCH_COUNT,
    ) -> float:
        """Compute form score for a team based on recent results.

        Ported from pldashboard predictions/form.py calc_form().

        Args:
            team_name: Name of the team
            recent_fixtures: Finished fixtures involving this team, sorted by date ascending
            team_ratings: {team_name: rating} dict
            num_matches: How many recent matches to consider (default 20)

        Returns:
            Form value in [0, 1]. 0.5 = neutral.
        """
        # Take only the last N matches
        matches = recent_fixtures[-num_matches:] if len(recent_fixtures) > num_matches else recent_fixtures

        if not matches:
            return 0.5

        # Linear weights from 0.2 to 1.0 — oldest match is 0.2, newest is 1.0
        weights = np.linspace(
            settings.FORM_WEIGHT_MIN,
            settings.FORM_WEIGHT_MAX,
            len(matches),
        )
        weights = weights / weights.sum()  # Normalize to sum to 1

        form = 0.5
        for fixture, weight in zip(matches, weights):
            if fixture.home_team_name == team_name:
                scored = fixture.home_goals or 0
                conceded = fixture.away_goals or 0
                opposition = fixture.away_team_name
            elif fixture.away_team_name == team_name:
                scored = fixture.away_goals or 0
                conceded = fixture.home_goals or 0
                opposition = fixture.home_team_name
            else:
                continue

            gd = scored - conceded
            opposition_rating = team_ratings.get(opposition, 0.0)
            form += opposition_rating * gd * weight

        return min(max(0.0, form), 1.0)

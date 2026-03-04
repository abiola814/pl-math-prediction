"""Corner predictor — NEW (no pldashboard equivalent).

Predicts total match corners using:
1. Team corner profiles (avg for/against, home/away splits)
2. Home advantage factor
3. Form and team rating adjustments
4. Poisson distribution for over/under lines
"""

from dataclasses import dataclass

from scipy.stats import poisson

from app.config import settings
from app.data.corner_stats import CornerProfile


@dataclass
class CornerPrediction:
    predicted_total: float
    home_corners: float
    away_corners: float
    over_85: float
    over_95: float
    over_105: float
    over_115: float
    recommended_line: float
    recommended_pick: str   # e.g. "Over 9.5"
    confidence: float


class CornerPredictor:
    HOME_ADVANTAGE_FACTOR = settings.CORNER_HOME_ADVANTAGE_FACTOR  # 1.15

    def predict(
        self,
        home_profile: CornerProfile,
        away_profile: CornerProfile,
        home_form: float,
        away_form: float,
        home_rating: float,
        away_rating: float,
    ) -> CornerPrediction:
        """Generate corner prediction for a match."""
        # Estimate each team's expected corners
        home_corners = self._estimate_team_corners(
            home_profile, away_profile, is_home=True
        )
        away_corners = self._estimate_team_corners(
            away_profile, home_profile, is_home=False
        )

        # Apply home advantage
        home_corners *= self.HOME_ADVANTAGE_FACTOR

        # Form adjustment: teams in better form push forward more
        home_corners = self._apply_form_adjustment(home_corners, home_form)
        away_corners = self._apply_form_adjustment(away_corners, away_form)

        # Rating mismatch adjustment: bigger mismatches produce more corners
        # (dominant team attacks, weaker team counters)
        rating_diff = abs(home_rating - away_rating)
        mismatch_factor = 1.0 + rating_diff * 0.1  # Up to ~10% more corners
        home_corners *= mismatch_factor
        away_corners *= mismatch_factor

        predicted_total = home_corners + away_corners

        # Poisson-based over/under probabilities
        over_under = self._compute_poisson_over_under(predicted_total)

        # Pick best line
        recommended_line, recommended_pick, confidence = self._select_best_line(over_under)

        return CornerPrediction(
            predicted_total=round(predicted_total, 1),
            home_corners=round(home_corners, 1),
            away_corners=round(away_corners, 1),
            over_85=round(over_under.get(8.5, 0.5), 4),
            over_95=round(over_under.get(9.5, 0.5), 4),
            over_105=round(over_under.get(10.5, 0.5), 4),
            over_115=round(over_under.get(11.5, 0.5), 4),
            recommended_line=recommended_line,
            recommended_pick=recommended_pick,
            confidence=round(confidence, 4),
        )

    def _estimate_team_corners(
        self,
        team_profile: CornerProfile,
        opponent_profile: CornerProfile,
        is_home: bool,
    ) -> float:
        """Estimate corners for one team.

        Uses the average of:
        - Team's avg corners won (in the appropriate venue)
        - Opponent's avg corners conceded (in the opposite venue)
        """
        if is_home:
            team_avg = team_profile.avg_corners_for_home
            opp_conceded = opponent_profile.avg_corners_against_away
        else:
            team_avg = team_profile.avg_corners_for_away
            opp_conceded = opponent_profile.avg_corners_against_home

        return (team_avg + opp_conceded) / 2

    @staticmethod
    def _apply_form_adjustment(corners: float, form: float) -> float:
        """Better form (> 0.5) means more attacking, more corners.

        form=0.5 → no change, form=1.0 → +10%, form=0.0 → -10%
        """
        adjustment = 1.0 + (form - 0.5) * 0.2
        return corners * adjustment

    @staticmethod
    def _compute_poisson_over_under(expected_total: float) -> dict[float, float]:
        """Use Poisson CDF to compute P(corners > line) for standard lines.

        Corners roughly follow a Poisson distribution, making this a
        principled approach for over/under calculations.
        """
        lines = [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
        result = {}
        for line in lines:
            # P(X > line) = 1 - P(X <= floor(line)) = 1 - CDF(floor(line))
            result[line] = float(1.0 - poisson.cdf(int(line), expected_total))
        return result

    @staticmethod
    def _select_best_line(
        over_under: dict[float, float],
    ) -> tuple[float, str, float]:
        """Pick the best Over corner line.

        Always recommends Over — picks the highest line where
        probability is 50%+.
        """
        best_line = 7.5  # Default fallback
        best_pick = "Over 7.5"
        best_conf = over_under.get(7.5, 0.5)

        # Check lines from highest to lowest, pick highest with 50%+
        for line in sorted(over_under.keys(), reverse=True):
            over_prob = over_under[line]
            if over_prob >= 0.50:
                return line, f"Over {line}", over_prob

        # Fallback: pick the lowest line (most likely to hit)
        lowest = min(over_under.keys())
        return lowest, f"Over {lowest}", over_under[lowest]

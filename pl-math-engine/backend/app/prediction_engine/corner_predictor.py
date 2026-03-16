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
    over_65: float
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

        # Rating mismatch: stronger team wins more corners (attacking dominance),
        # weaker team gets slightly fewer (sitting deeper, conceding possession)
        rating_diff = abs(home_rating - away_rating)
        if home_rating > away_rating:
            home_corners *= 1.0 + rating_diff * 0.15  # Stronger team pushes forward
            away_corners *= 1.0 - rating_diff * 0.05  # Weaker team sits deeper
        elif away_rating > home_rating:
            away_corners *= 1.0 + rating_diff * 0.15
            home_corners *= 1.0 - rating_diff * 0.05

        predicted_total = home_corners + away_corners

        # Poisson-based over/under probabilities
        over_under = self._compute_poisson_over_under(predicted_total)

        # Pick best line
        recommended_line, recommended_pick, confidence = self._select_best_line(over_under)

        return CornerPrediction(
            predicted_total=round(predicted_total, 1),
            home_corners=round(home_corners, 1),
            away_corners=round(away_corners, 1),
            over_65=round(over_under.get(6.5, 0.5), 4),
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

        form=0.5 → no change, form=1.0 → +15%, form=0.0 → -15%
        """
        adjustment = 1.0 + (form - 0.5) * 0.3
        return corners * adjustment

    @staticmethod
    def _compute_poisson_over_under(expected_total: float) -> dict[float, float]:
        """Use Poisson CDF to compute P(corners > line) for standard lines.

        Corners roughly follow a Poisson distribution, making this a
        principled approach for over/under calculations.
        """
        lines = [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5]
        result = {}
        for line in lines:
            # P(X > line) = 1 - P(X <= floor(line)) = 1 - CDF(floor(line))
            result[line] = float(1.0 - poisson.cdf(int(line), expected_total))
        return result

    @staticmethod
    def _select_best_line(
        over_under: dict[float, float],
    ) -> tuple[float, str, float]:
        """Pick the safest Over corner line with good value.

        Prefers the safest viable line — only recommends a higher
        line if confidence is very strong (65%+).
        """
        # Start from safest line and only go higher if very confident
        for line in sorted(over_under.keys()):
            over_prob = over_under[line]
            if over_prob >= 0.55:
                # Check if a higher line has strong enough confidence
                next_lines = [l for l in sorted(over_under.keys()) if l > line]
                for next_line in next_lines:
                    if over_under[next_line] >= 0.65:
                        line = next_line
                        over_prob = over_under[next_line]
                    else:
                        break
                return line, f"Over {line}", over_prob

        # Fallback: pick the lowest line (most likely to hit)
        lowest = min(over_under.keys())
        return lowest, f"Over {lowest}", over_under[lowest]

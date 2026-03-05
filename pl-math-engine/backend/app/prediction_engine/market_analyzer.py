"""Market analyzer — derives Over/Under and BTTS from scoreline distribution.

This is NEW — no pldashboard equivalent. It sums probabilities from the
scoreline distribution to compute betting market recommendations.

Logic:
  over_15 = Σ P(scorelines where total > 1.5)
  over_25 = Σ P(scorelines where total > 2.5)
  btts_yes = Σ P(scorelines where home ≥ 1 AND away ≥ 1)
"""

from dataclasses import dataclass

from app.prediction_engine.scoreline import Scoreline


@dataclass
class MarketPrediction:
    # Match Over/Under probabilities
    over_05: float
    over_15: float
    over_25: float
    over_35: float

    # Home team Over/Under probabilities
    home_over_05: float
    home_over_15: float
    home_over_25: float

    # Away team Over/Under probabilities
    away_over_05: float
    away_over_15: float
    away_over_25: float

    # BTTS
    btts_yes: float
    btts_no: float

    # Match recommendations
    recommended_market: str        # e.g. "Over 2.5 Goals"
    recommended_confidence: float
    btts_recommendation: str       # "BTTS Yes" or "BTTS No"
    btts_confidence: float

    # Home/Away team recommendations
    home_recommended: str          # e.g. "Home Over 0.5 Goals"
    home_recommended_confidence: float
    away_recommended: str          # e.g. "Away Over 0.5 Goals"
    away_recommended_confidence: float


class MarketAnalyzer:
    """Derives betting market predictions from the scoreline probability distribution."""

    # Minimum confidence to make a recommendation
    OVER_25_THRESHOLD = 0.55
    OVER_15_THRESHOLD = 0.60
    UNDER_25_THRESHOLD = 0.60
    UNDER_15_THRESHOLD = 0.55
    BTTS_THRESHOLD = 0.55

    def analyze(self, scoreline_probs: dict[Scoreline, float]) -> MarketPrediction:
        """Compute all market probabilities from the scoreline distribution."""
        over_05 = 0.0
        over_15 = 0.0
        over_25 = 0.0
        over_35 = 0.0
        btts_yes = 0.0

        # Home/away team individual goal probabilities
        home_over_05 = 0.0
        home_over_15 = 0.0
        home_over_25 = 0.0
        away_over_05 = 0.0
        away_over_15 = 0.0
        away_over_25 = 0.0

        for scoreline, prob in scoreline_probs.items():
            total = scoreline.total_goals
            if total > 0.5:
                over_05 += prob
            if total > 1.5:
                over_15 += prob
            if total > 2.5:
                over_25 += prob
            if total > 3.5:
                over_35 += prob
            if scoreline.both_scored:
                btts_yes += prob

            # Home team goals
            if scoreline.home_goals > 0.5:
                home_over_05 += prob
            if scoreline.home_goals > 1.5:
                home_over_15 += prob
            if scoreline.home_goals > 2.5:
                home_over_25 += prob

            # Away team goals
            if scoreline.away_goals > 0.5:
                away_over_05 += prob
            if scoreline.away_goals > 1.5:
                away_over_15 += prob
            if scoreline.away_goals > 2.5:
                away_over_25 += prob

        btts_no = 1.0 - btts_yes

        # Pick best match-level over/under recommendation
        recommended_market, recommended_confidence = self._select_best_market(
            over_05, over_15, over_25, over_35
        )

        # BTTS recommendation
        btts_recommendation, btts_confidence = self._determine_btts(btts_yes)

        # Home/away team recommendations
        home_recommended, home_rec_conf = self._select_team_market(
            "Home", home_over_05, home_over_15, home_over_25
        )
        away_recommended, away_rec_conf = self._select_team_market(
            "Away", away_over_05, away_over_15, away_over_25
        )

        return MarketPrediction(
            over_05=round(over_05, 4),
            over_15=round(over_15, 4),
            over_25=round(over_25, 4),
            over_35=round(over_35, 4),
            home_over_05=round(home_over_05, 4),
            home_over_15=round(home_over_15, 4),
            home_over_25=round(home_over_25, 4),
            away_over_05=round(away_over_05, 4),
            away_over_15=round(away_over_15, 4),
            away_over_25=round(away_over_25, 4),
            btts_yes=round(btts_yes, 4),
            btts_no=round(btts_no, 4),
            recommended_market=recommended_market,
            recommended_confidence=round(recommended_confidence, 4),
            btts_recommendation=btts_recommendation,
            btts_confidence=round(btts_confidence, 4),
            home_recommended=home_recommended,
            home_recommended_confidence=round(home_rec_conf, 4),
            away_recommended=away_recommended,
            away_recommended_confidence=round(away_rec_conf, 4),
        )

    def _select_best_market(
        self,
        over_05: float,
        over_15: float,
        over_25: float,
        over_35: float,
    ) -> tuple[str, float]:
        """Pick the best Over/Under line for match goals.

        Uses the expected goal total (derived from probabilities) to choose the
        most relevant line, then picks Over or Under based on which side has
        stronger probability. This avoids always picking trivial lines like
        Over 1.5 which hit ~85% of matches.

        Strategy: pick the line where the probability is furthest from 50%
        (strongest edge), but only from meaningful lines (2.5 and 3.5).
        Fall back to 1.5 only in low-scoring match scenarios.
        """
        # For each line, compute the "edge" = |prob - 0.5|
        # Higher edge = more confident pick
        lines = [
            ("Over 3.5 Goals", over_35, "Under 3.5 Goals", 1.0 - over_35),
            ("Over 2.5 Goals", over_25, "Under 2.5 Goals", 1.0 - over_25),
            ("Over 1.5 Goals", over_15, "Under 1.5 Goals", 1.0 - over_15),
        ]

        best_label = "Over 2.5 Goals"
        best_prob = over_25
        best_edge = 0.0

        for over_label, over_prob, under_label, under_prob in lines:
            # Pick the stronger side for this line
            if over_prob >= under_prob:
                label, prob = over_label, over_prob
            else:
                label, prob = under_label, under_prob

            edge = abs(prob - 0.5)

            # Prefer 2.5 and 3.5 lines over 1.5 (more useful picks)
            # Only use 1.5 if it has a much stronger edge
            if "1.5" in label:
                edge *= 0.7  # discount trivial lines

            if edge > best_edge:
                best_edge = edge
                best_label = label
                best_prob = prob

        return best_label, best_prob

    def _select_team_market(
        self,
        side: str,  # "Home" or "Away"
        over_05: float,
        over_15: float,
        over_25: float,
    ) -> tuple[str, float]:
        """Pick the best Over/Under line for a specific team's goals.

        For each line, picks whichever side has the highest probability.
        """
        candidates = [
            (f"{side} Over 2.5 Goals", over_25),
            (f"{side} Under 2.5 Goals", 1.0 - over_25),
            (f"{side} Over 1.5 Goals", over_15),
            (f"{side} Under 1.5 Goals", 1.0 - over_15),
            (f"{side} Over 0.5 Goals", over_05),
            (f"{side} Under 0.5 Goals", 1.0 - over_05),
        ]

        best_label, best_prob = max(candidates, key=lambda c: c[1])
        return best_label, best_prob

    def _determine_btts(self, btts_yes: float) -> tuple[str, float]:
        """Determine BTTS recommendation."""
        if btts_yes >= self.BTTS_THRESHOLD:
            return "BTTS Yes", btts_yes
        elif (1.0 - btts_yes) >= self.BTTS_THRESHOLD:
            return "BTTS No", 1.0 - btts_yes
        else:
            # Low confidence — pick the higher one
            if btts_yes >= 0.5:
                return "BTTS Yes", btts_yes
            return "BTTS No", 1.0 - btts_yes

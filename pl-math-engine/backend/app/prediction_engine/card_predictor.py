"""Card predictor — predicts total match yellow cards.

Uses:
1. Team card profiles (avg for/against, home/away splits)
2. Away team aggression factor (away teams typically pick up more cards)
3. Rating mismatch adjustment (bigger gap = more fouls from weaker side)
4. Poisson distribution for over/under card lines
"""

from dataclasses import dataclass

from scipy.stats import poisson

from app.data.card_stats import CardProfile


@dataclass
class CardPrediction:
    predicted_total: float
    home_cards: float
    away_cards: float
    over_25: float
    over_35: float
    over_45: float
    over_55: float
    recommended_line: float
    recommended_pick: str   # e.g. "Over 3.5 Cards"
    confidence: float


class CardPredictor:
    # Away teams pick up ~10% more yellows on average
    AWAY_AGGRESSION_FACTOR = 1.10

    def predict(
        self,
        home_profile: CardProfile,
        away_profile: CardProfile,
        home_form: float,
        away_form: float,
        home_rating: float,
        away_rating: float,
    ) -> CardPrediction:
        """Generate yellow card prediction for a match."""
        # Estimate each team's expected yellow cards
        home_cards = self._estimate_team_cards(
            home_profile, away_profile, is_home=True
        )
        away_cards = self._estimate_team_cards(
            away_profile, home_profile, is_home=False
        )

        # Away teams pick up more cards (travel, crowd pressure, etc.)
        away_cards *= self.AWAY_AGGRESSION_FACTOR

        # Form adjustment: teams in bad form tend to foul more (frustrated play)
        home_cards = self._apply_form_adjustment(home_cards, home_form)
        away_cards = self._apply_form_adjustment(away_cards, away_form)

        # Rating mismatch: weaker team fouls more to stop the stronger team
        rating_diff = abs(home_rating - away_rating)
        if home_rating > away_rating:
            away_cards *= 1.0 + rating_diff * 0.15
        else:
            home_cards *= 1.0 + rating_diff * 0.15

        predicted_total = home_cards + away_cards

        # Poisson-based over/under probabilities
        over_under = self._compute_poisson_over_under(predicted_total)

        # Pick best line
        recommended_line, recommended_pick, confidence = self._select_best_line(over_under)

        return CardPrediction(
            predicted_total=round(predicted_total, 1),
            home_cards=round(home_cards, 1),
            away_cards=round(away_cards, 1),
            over_25=round(over_under.get(2.5, 0.5), 4),
            over_35=round(over_under.get(3.5, 0.5), 4),
            over_45=round(over_under.get(4.5, 0.5), 4),
            over_55=round(over_under.get(5.5, 0.5), 4),
            recommended_line=recommended_line,
            recommended_pick=recommended_pick,
            confidence=round(confidence, 4),
        )

    def _estimate_team_cards(
        self,
        team_profile: CardProfile,
        opponent_profile: CardProfile,
        is_home: bool,
    ) -> float:
        """Estimate yellow cards for one team.

        Uses the average of:
        - Team's avg yellows received (in the appropriate venue)
        - Opponent's avg yellows their opponents receive (in the opposite venue)
        """
        if is_home:
            team_avg = team_profile.avg_yellows_for_home
            opp_conceded = opponent_profile.avg_yellows_against_away
        else:
            team_avg = team_profile.avg_yellows_for_away
            opp_conceded = opponent_profile.avg_yellows_against_home

        return (team_avg + opp_conceded) / 2

    @staticmethod
    def _apply_form_adjustment(cards: float, form: float) -> float:
        """Worse form (< 0.5) means more frustrated play, more fouls → more cards.

        form=0.5 → no change, form=0.0 → +15%, form=1.0 → -15%
        This is INVERTED compared to corners — bad form = more cards.
        """
        adjustment = 1.0 - (form - 0.5) * 0.3
        return cards * adjustment

    @staticmethod
    def _compute_poisson_over_under(expected_total: float) -> dict[float, float]:
        """Use Poisson CDF to compute P(cards > line) for standard lines."""
        lines = [1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
        result = {}
        for line in lines:
            result[line] = float(1.0 - poisson.cdf(int(line), expected_total))
        return result

    @staticmethod
    def _select_best_line(
        over_under: dict[float, float],
    ) -> tuple[float, str, float]:
        """Pick the best Over card line.

        Always recommends Over — picks the highest line where
        probability is 50%+.
        """
        # Check lines from highest to lowest, pick highest with 50%+
        for line in sorted(over_under.keys(), reverse=True):
            over_prob = over_under[line]
            if over_prob >= 0.50:
                return line, f"Over {line} Cards", over_prob

        # Fallback: pick the lowest line (most likely to hit)
        lowest = min(over_under.keys())
        return lowest, f"Over {lowest} Cards", over_under[lowest]

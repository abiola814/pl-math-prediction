"""Tests for the card predictor."""

from app.data.card_stats import CardProfile
from app.prediction_engine.card_predictor import CardPredictor


class TestCardPredictor:
    def _default_profiles(self):
        home = CardProfile(
            avg_yellows_for_home=1.8,
            avg_yellows_for_away=2.2,
            avg_yellows_against_home=1.5,
            avg_yellows_against_away=2.0,
            total_matches=20,
        )
        away = CardProfile(
            avg_yellows_for_home=2.0,
            avg_yellows_for_away=2.5,
            avg_yellows_against_home=1.8,
            avg_yellows_against_away=1.6,
            total_matches=20,
        )
        return home, away

    def test_predict_returns_valid_result(self):
        predictor = CardPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.6, away_form=0.5,
            home_rating=0.7, away_rating=0.5,
        )

        assert result.predicted_total > 0
        assert result.home_cards > 0
        assert result.away_cards > 0
        assert abs(result.predicted_total - (result.home_cards + result.away_cards)) < 0.2

    def test_away_team_gets_more_cards(self):
        """Away teams typically pick up more yellows (crowd pressure, travel)."""
        predictor = CardPredictor()
        # Use identical profiles so the only difference is home/away
        profile = CardProfile(
            avg_yellows_for_home=2.0,
            avg_yellows_for_away=2.0,
            avg_yellows_against_home=2.0,
            avg_yellows_against_away=2.0,
            total_matches=20,
        )

        result = predictor.predict(
            profile, profile,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        # Away team should have more cards due to aggression factor
        assert result.away_cards > result.home_cards

    def test_bad_form_increases_cards(self):
        """Teams in bad form tend to foul more (frustrated play)."""
        predictor = CardPredictor()
        home_p, away_p = self._default_profiles()

        result_bad_form = predictor.predict(
            home_p, away_p,
            home_form=0.1, away_form=0.1,
            home_rating=0.5, away_rating=0.5,
        )
        result_good_form = predictor.predict(
            home_p, away_p,
            home_form=0.9, away_form=0.9,
            home_rating=0.5, away_rating=0.5,
        )

        assert result_bad_form.predicted_total > result_good_form.predicted_total

    def test_over_under_probabilities_are_valid(self):
        predictor = CardPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        # Over probabilities should decrease as the line increases
        assert result.over_25 >= result.over_35
        assert result.over_35 >= result.over_45
        assert result.over_45 >= result.over_55

        # All probabilities should be between 0 and 1
        for prob in [result.over_25, result.over_35, result.over_45, result.over_55]:
            assert 0 <= prob <= 1

    def test_recommended_pick_is_valid(self):
        predictor = CardPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        assert "Over" in result.recommended_pick
        assert "Cards" in result.recommended_pick
        assert result.confidence > 0

    def test_rating_mismatch_increases_weaker_team_cards(self):
        """When there's a big rating gap, the weaker team fouls more."""
        predictor = CardPredictor()
        home_p, away_p = self._default_profiles()

        result_mismatch = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.9, away_rating=0.2,
        )
        result_even = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        # Mismatch should produce more total cards
        assert result_mismatch.predicted_total > result_even.predicted_total

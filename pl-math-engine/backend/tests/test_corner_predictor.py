"""Tests for the corner predictor."""

from app.data.corner_stats import CornerProfile
from app.prediction_engine.corner_predictor import CornerPredictor


class TestCornerPredictor:
    def _default_profiles(self):
        home = CornerProfile(
            avg_corners_for_home=6.0,
            avg_corners_for_away=4.5,
            avg_corners_against_home=4.0,
            avg_corners_against_away=5.5,
            total_matches=20,
        )
        away = CornerProfile(
            avg_corners_for_home=5.5,
            avg_corners_for_away=4.0,
            avg_corners_against_home=5.0,
            avg_corners_against_away=4.5,
            total_matches=20,
        )
        return home, away

    def test_predict_returns_valid_result(self):
        predictor = CornerPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.6, away_form=0.5,
            home_rating=0.7, away_rating=0.5,
        )

        assert result.predicted_total > 0
        assert result.home_corners > 0
        assert result.away_corners > 0
        assert abs(result.predicted_total - (result.home_corners + result.away_corners)) < 0.2

    def test_home_advantage_increases_home_corners(self):
        predictor = CornerPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        # Home team should have more corners due to home advantage factor
        assert result.home_corners > result.away_corners

    def test_better_form_increases_corners(self):
        predictor = CornerPredictor()
        home_p, away_p = self._default_profiles()

        result_good_form = predictor.predict(
            home_p, away_p,
            home_form=0.9, away_form=0.9,
            home_rating=0.5, away_rating=0.5,
        )
        result_bad_form = predictor.predict(
            home_p, away_p,
            home_form=0.1, away_form=0.1,
            home_rating=0.5, away_rating=0.5,
        )

        assert result_good_form.predicted_total > result_bad_form.predicted_total

    def test_over_under_probabilities_are_valid(self):
        predictor = CornerPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        # Over probabilities should decrease as the line increases
        assert result.over_85 >= result.over_95
        assert result.over_95 >= result.over_105
        assert result.over_105 >= result.over_115

        # All probabilities should be between 0 and 1
        for prob in [result.over_85, result.over_95, result.over_105, result.over_115]:
            assert 0 <= prob <= 1

    def test_recommended_pick_is_valid(self):
        predictor = CornerPredictor()
        home_p, away_p = self._default_profiles()

        result = predictor.predict(
            home_p, away_p,
            home_form=0.5, away_form=0.5,
            home_rating=0.5, away_rating=0.5,
        )

        assert "Over" in result.recommended_pick
        assert result.confidence > 0

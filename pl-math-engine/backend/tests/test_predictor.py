"""Tests for the core scoreline predictor."""

from app.prediction_engine.scoreline import Scoreline
from app.prediction_engine.predictor import ScorelinePredictor
from app.models.fixture import Fixture
from datetime import datetime


def _make_fixture(home: str, away: str, hg: int, ag: int, season: int = 2024) -> Fixture:
    f = Fixture()
    f.api_id = hash(f"{home}{away}{hg}{ag}{season}") % 100000
    f.home_team_name = home
    f.away_team_name = away
    f.home_goals = hg
    f.away_goals = ag
    f.home_team_id = hash(home) % 1000
    f.away_team_id = hash(away) % 1000
    f.date = datetime(2024, 1, 1)
    f.season = season
    f.status = "FT"
    return f


class TestScoreline:
    def test_properties(self):
        s = Scoreline(2, 1)
        assert s.total_goals == 3
        assert s.home_win is True
        assert s.away_win is False
        assert s.draw is False
        assert s.both_scored is True
        assert s.result == "H"

    def test_draw(self):
        s = Scoreline(1, 1)
        assert s.draw is True
        assert s.result == "D"
        assert s.both_scored is True

    def test_away_win(self):
        s = Scoreline(0, 2)
        assert s.away_win is True
        assert s.result == "A"
        assert s.both_scored is False

    def test_no_goals(self):
        s = Scoreline(0, 0)
        assert s.total_goals == 0
        assert s.both_scored is False
        assert s.draw is True

    def test_equality(self):
        assert Scoreline(2, 1) == Scoreline(2, 1)
        assert Scoreline(2, 1) != Scoreline(1, 2)

    def test_hash(self):
        d = {Scoreline(2, 1): 5, Scoreline(1, 0): 3}
        assert d[Scoreline(2, 1)] == 5


class TestScorelinePredictor:
    def _create_predictor(self):
        ratings = {"TeamA": 0.8, "TeamB": 0.5, "TeamC": 0.3}
        advantages = {"TeamA": 0.1, "TeamB": 0.05, "TeamC": 0.0}
        return ScorelinePredictor(ratings, advantages)

    def _create_fixtures(self):
        """Create a set of historical fixtures."""
        fixtures_a = [
            _make_fixture("TeamA", "TeamB", 2, 1),
            _make_fixture("TeamA", "TeamC", 3, 0),
            _make_fixture("TeamC", "TeamA", 0, 2),
            _make_fixture("TeamA", "TeamB", 1, 1),
            _make_fixture("TeamB", "TeamA", 1, 2),
        ]
        fixtures_b = [
            _make_fixture("TeamB", "TeamC", 1, 0),
            _make_fixture("TeamA", "TeamB", 2, 1),
            _make_fixture("TeamB", "TeamA", 1, 2),
            _make_fixture("TeamC", "TeamB", 2, 2),
            _make_fixture("TeamA", "TeamB", 1, 1),
        ]
        h2h = [
            _make_fixture("TeamA", "TeamB", 2, 1),
            _make_fixture("TeamB", "TeamA", 1, 2),
            _make_fixture("TeamA", "TeamB", 1, 1),
        ]
        return fixtures_a, fixtures_b, h2h

    def test_compute_probabilities_returns_valid_distribution(self):
        predictor = self._create_predictor()
        fa, fb, h2h = self._create_fixtures()

        probs = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", fa, fb, h2h,
            home_form=0.7, away_form=0.4,
        )

        assert len(probs) > 0
        total_prob = sum(probs.values())
        assert abs(total_prob - 1.0) < 0.001, f"Total prob: {total_prob}"
        assert all(p >= 0 for p in probs.values())

    def test_predict_score_returns_scoreline(self):
        predictor = self._create_predictor()
        fa, fb, h2h = self._create_fixtures()

        probs = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", fa, fb, h2h,
            home_form=0.7, away_form=0.4,
        )
        score = predictor.predict_score(probs)

        assert score is not None
        assert isinstance(score, Scoreline)
        assert score.home_goals >= 0
        assert score.away_goals >= 0

    def test_top_scorelines(self):
        predictor = self._create_predictor()
        fa, fb, h2h = self._create_fixtures()

        probs = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", fa, fb, h2h,
            home_form=0.6, away_form=0.5,
        )
        top = predictor.top_scorelines(probs, n=3)

        assert len(top) <= 3
        # Should be sorted descending by probability
        probs_only = [p for _, p in top]
        assert probs_only == sorted(probs_only, reverse=True)

    def test_form_affects_prediction(self):
        """Higher home form should increase home win probability."""
        predictor = self._create_predictor()
        fa, fb, h2h = self._create_fixtures()

        # High home form
        probs_high = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", fa, fb, h2h,
            home_form=0.9, away_form=0.2,
        )
        # Low home form
        probs_low = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", fa, fb, h2h,
            home_form=0.2, away_form=0.9,
        )

        # Sum up home win probabilities
        home_win_high = sum(
            p for s, p in probs_high.items() if s.home_win
        )
        home_win_low = sum(
            p for s, p in probs_low.items() if s.home_win
        )

        assert home_win_high > home_win_low

    def test_empty_fixtures_returns_empty(self):
        predictor = self._create_predictor()
        probs = predictor.compute_scoreline_probabilities(
            "TeamA", "TeamB", [], [], [],
            home_form=0.5, away_form=0.5,
        )
        assert probs == {}

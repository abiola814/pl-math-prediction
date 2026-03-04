"""Tests for the market analyzer (Over/Under + BTTS)."""

from app.prediction_engine.market_analyzer import MarketAnalyzer
from app.prediction_engine.scoreline import Scoreline


class TestMarketAnalyzer:
    def _high_scoring_distribution(self) -> dict[Scoreline, float]:
        """A distribution biased toward high-scoring matches."""
        return {
            Scoreline(3, 2): 0.15,
            Scoreline(2, 1): 0.20,
            Scoreline(2, 2): 0.10,
            Scoreline(1, 1): 0.10,
            Scoreline(3, 1): 0.10,
            Scoreline(1, 0): 0.10,
            Scoreline(2, 0): 0.08,
            Scoreline(0, 1): 0.07,
            Scoreline(0, 0): 0.05,
            Scoreline(4, 1): 0.05,
        }

    def _low_scoring_distribution(self) -> dict[Scoreline, float]:
        """A distribution biased toward low-scoring matches."""
        return {
            Scoreline(0, 0): 0.25,
            Scoreline(1, 0): 0.25,
            Scoreline(0, 1): 0.20,
            Scoreline(1, 1): 0.15,
            Scoreline(2, 0): 0.05,
            Scoreline(0, 2): 0.05,
            Scoreline(2, 1): 0.05,
        }

    def test_probabilities_sum_correctly(self):
        analyzer = MarketAnalyzer()
        dist = self._high_scoring_distribution()
        market = analyzer.analyze(dist)

        # Over 0.5 should be higher than Over 1.5, etc.
        assert market.over_05 >= market.over_15
        assert market.over_15 >= market.over_25
        assert market.over_25 >= market.over_35

        # BTTS yes + no should sum to ~1
        assert abs(market.btts_yes + market.btts_no - 1.0) < 0.01

    def test_high_scoring_recommends_over(self):
        analyzer = MarketAnalyzer()
        dist = self._high_scoring_distribution()
        market = analyzer.analyze(dist)

        assert "Over" in market.recommended_market
        assert market.recommended_confidence > 0.5

    def test_low_scoring_recommends_low_over(self):
        analyzer = MarketAnalyzer()
        dist = self._low_scoring_distribution()
        market = analyzer.analyze(dist)

        # Low scoring matches should get Over 0.5 or Over 1.5 (always Over)
        assert "Over" in market.recommended_market
        assert "0.5" in market.recommended_market or "1.5" in market.recommended_market

    def test_btts_high_scoring(self):
        analyzer = MarketAnalyzer()
        dist = self._high_scoring_distribution()
        market = analyzer.analyze(dist)

        # High scoring: many scorelines have both teams scoring
        assert market.btts_yes > 0.4

    def test_btts_low_scoring(self):
        analyzer = MarketAnalyzer()
        dist = self._low_scoring_distribution()
        market = analyzer.analyze(dist)

        # Low scoring: 0-0, 1-0, 0-1 dominate — BTTS should be low
        assert market.btts_yes < 0.3

    def test_empty_distribution(self):
        analyzer = MarketAnalyzer()
        market = analyzer.analyze({})

        assert market.over_05 == 0.0
        assert market.btts_yes == 0.0
        assert market.home_over_05 == 0.0
        assert market.away_over_05 == 0.0

    def test_home_over_probabilities_high_scoring(self):
        analyzer = MarketAnalyzer()
        dist = self._high_scoring_distribution()
        market = analyzer.analyze(dist)

        # Home team scores in most high-scoring scenarios
        assert market.home_over_05 > 0.7
        assert market.home_over_05 >= market.home_over_15
        assert market.home_over_15 >= market.home_over_25

    def test_away_over_probabilities_low_scoring(self):
        analyzer = MarketAnalyzer()
        dist = self._low_scoring_distribution()
        market = analyzer.analyze(dist)

        # Away team scores less in low-scoring games
        assert market.away_over_05 < 0.5

    def test_home_away_recommendations_exist(self):
        analyzer = MarketAnalyzer()
        dist = self._high_scoring_distribution()
        market = analyzer.analyze(dist)

        assert "Home" in market.home_recommended
        assert "Away" in market.away_recommended
        assert market.home_recommended_confidence > 0.0
        assert market.away_recommended_confidence > 0.0

    def test_one_sided_scoreline_home_dominance(self):
        """When home team scores a lot, it gets a higher Over line."""
        analyzer = MarketAnalyzer()
        dist = {
            Scoreline(3, 0): 0.30,
            Scoreline(2, 0): 0.25,
            Scoreline(1, 0): 0.20,
            Scoreline(2, 1): 0.15,
            Scoreline(0, 0): 0.10,
        }
        market = analyzer.analyze(dist)

        # Home scores in 90% of scenarios
        assert market.home_over_05 >= 0.90
        # Away only scores in 15% of scenarios
        assert market.away_over_05 <= 0.20

        # Both always recommend Over
        assert "Over" in market.home_recommended
        assert "Over" in market.away_recommended
        # Home should get a higher line than away
        assert market.home_recommended_confidence > market.away_recommended_confidence

    def test_balanced_score_both_teams_over(self):
        """For a balanced 1-1 type prediction, both teams get Over 0.5."""
        analyzer = MarketAnalyzer()
        dist = {
            Scoreline(1, 1): 0.30,
            Scoreline(1, 0): 0.15,
            Scoreline(0, 1): 0.15,
            Scoreline(2, 1): 0.15,
            Scoreline(1, 2): 0.10,
            Scoreline(0, 0): 0.10,
            Scoreline(2, 2): 0.05,
        }
        market = analyzer.analyze(dist)

        # Both teams score in most scenarios
        assert market.home_over_05 > 0.7
        assert market.away_over_05 > 0.7
        # Both should recommend Over 0.5
        assert "Over 0.5" in market.home_recommended
        assert "Over 0.5" in market.away_recommended

    def test_high_scoring_team_gets_higher_over_line(self):
        """When a team scores 2+ goals in most scenarios, pick Over 1.5."""
        analyzer = MarketAnalyzer()
        dist = {
            Scoreline(2, 0): 0.25,
            Scoreline(3, 1): 0.20,
            Scoreline(2, 1): 0.20,
            Scoreline(2, 2): 0.15,
            Scoreline(3, 0): 0.10,
            Scoreline(1, 0): 0.10,
        }
        market = analyzer.analyze(dist)

        # Home scores 2+ in 90% of scenarios (all except 1-0)
        assert market.home_over_15 > 0.85
        assert "Over 1.5" in market.home_recommended

    def test_low_scoring_away_still_over(self):
        """Even when away barely scores, recommendation is still Over 0.5."""
        analyzer = MarketAnalyzer()
        dist = {
            Scoreline(1, 0): 0.40,
            Scoreline(2, 0): 0.20,
            Scoreline(1, 1): 0.10,
            Scoreline(0, 0): 0.15,
            Scoreline(0, 1): 0.10,
            Scoreline(3, 0): 0.05,
        }
        market = analyzer.analyze(dist)

        # Away Over 0.5 is only 20% — low confidence but still Over
        assert "Over 0.5" in market.away_recommended
        assert market.away_recommended_confidence < 0.30

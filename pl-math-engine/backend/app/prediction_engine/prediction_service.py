"""Prediction service — orchestrates all prediction components.

Pipeline:
1. DataService provides fixtures, standings, corner stats, card stats, injuries
2. TeamRatingCalculator computes ratings
3. HomeAdvantageCalculator computes home advantages
4. FormCalculator computes form for both teams
5. ScorelinePredictor produces scoreline probability distribution
6. MarketAnalyzer derives over/under + BTTS from distribution
7. CornerPredictor produces corner predictions
8. CardPredictor produces yellow card predictions
9. LLM Market Analyst gets ALL the data and makes its own market picks
10. Store prediction in DB for accuracy tracking
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.data.card_stats import CardStatsCalculator
from app.data.corner_stats import CornerStatsCalculator
from app.data.data_service import DataService
from app.data.form_calculator import FormCalculator
from app.data.home_advantages import HomeAdvantageCalculator
from app.data.team_ratings import TeamRatingCalculator
from app.models.fixture import Fixture
from app.models.fixture_stats import FixtureStatistics
from app.models.prediction import Prediction
from app.prediction_engine.card_predictor import CardPrediction, CardPredictor
from app.prediction_engine.corner_predictor import CornerPrediction, CornerPredictor
from app.prediction_engine.llm_adjuster import LLMMarketAnalyst, LLMMarketVerdict
from app.prediction_engine.market_analyzer import MarketAnalyzer, MarketPrediction
from app.prediction_engine.predictor import ScorelinePredictor
from app.prediction_engine.scoreline import Scoreline

logger = logging.getLogger(__name__)


@dataclass
class FullPrediction:
    """Complete prediction output for a single fixture."""
    fixture_api_id: int
    home_team: str
    away_team: str
    home_team_id: int
    away_team_id: int
    date: datetime

    # Score prediction
    predicted_score: Scoreline
    score_probability: float
    top_scorelines: list[tuple[str, float]]

    # Stats-based market predictions
    market: MarketPrediction

    # Corner prediction
    corners: CornerPrediction

    # Card prediction (yellow cards)
    cards: CardPrediction

    # LLM market verdict (the AI's own picks with reasoning)
    llm_verdict: Optional[LLMMarketVerdict]
    llm_insight: Optional[str]
    llm_adjustment_applied: bool


class PredictionService:
    def __init__(self, db: Session, llm_client=None):
        self.db = db
        self.data_service = DataService(db)
        self.form_calculator = FormCalculator()
        self.market_analyzer = MarketAnalyzer()
        self.corner_predictor = CornerPredictor()
        self.corner_stats_calc = CornerStatsCalculator()
        self.card_predictor = CardPredictor()
        self.card_stats_calc = CardStatsCalculator()
        self.llm_analyst = LLMMarketAnalyst(anthropic_client=llm_client)

    def _build_computed_data(self):
        """Compute team ratings and home advantages from cached DB data."""
        standings = self.data_service.get_standings_multi_season()
        team_ratings = TeamRatingCalculator().compute(
            standings, settings.CURRENT_SEASON
        )

        fixtures_by_season: dict[int, list[Fixture]] = {}
        for offset in range(settings.NUM_SEASONS):
            season = settings.CURRENT_SEASON - offset
            fixtures_by_season[season] = self.data_service.get_finished_fixtures(season)

        home_advantages = HomeAdvantageCalculator().compute(
            fixtures_by_season, settings.CURRENT_SEASON
        )

        return team_ratings, home_advantages, fixtures_by_season

    async def predict_fixture(self, fixture: Fixture) -> FullPrediction:
        """Generate a complete prediction for a single fixture."""
        home_team = fixture.home_team_name
        away_team = fixture.away_team_name

        # Step 1: Compute team ratings and home advantages
        team_ratings, home_advantages, _ = self._build_computed_data()

        # Step 2: Get historical fixtures for each team + H2H
        home_fixtures = self.data_service.get_team_fixtures(home_team)
        away_fixtures = self.data_service.get_team_fixtures(away_team)
        h2h_fixtures = self.data_service.get_h2h_fixtures(home_team, away_team)

        # Step 3: Calculate form
        home_form = self.form_calculator.calc_form(
            home_team, home_fixtures, team_ratings
        )
        away_form = self.form_calculator.calc_form(
            away_team, away_fixtures, team_ratings
        )

        # Step 4: Run core scoreline predictor
        predictor = ScorelinePredictor(team_ratings, home_advantages)
        scoreline_probs = predictor.compute_scoreline_probabilities(
            home_team, away_team,
            home_fixtures, away_fixtures, h2h_fixtures,
            home_form, away_form,
        )

        # Step 5: Get predicted score
        predicted_score = predictor.predict_score(scoreline_probs)
        if predicted_score is None:
            predicted_score = Scoreline(1, 0)

        score_prob = scoreline_probs.get(predicted_score, 0.0)
        top = predictor.top_scorelines(scoreline_probs, n=5)

        # Step 6: Stats-based market analysis
        market = self.market_analyzer.analyze(scoreline_probs)

        # Step 7: Corner prediction
        corners = self._predict_corners(
            fixture, home_form, away_form, team_ratings
        )

        # Step 8: Card prediction (yellow cards)
        cards = self._predict_cards(
            fixture, home_form, away_form, team_ratings
        )

        # Step 9: LLM market analysis — give it EVERYTHING and let it reason
        home_injuries = self.data_service.get_team_injuries(home_team)
        away_injuries = self.data_service.get_team_injuries(away_team)

        llm_verdict = await self.llm_analyst.analyze_match(
            home_team=home_team,
            away_team=away_team,
            predicted_score=predicted_score,
            stats_market=market,
            corners=corners,
            cards=cards,
            home_injuries=home_injuries,
            away_injuries=away_injuries,
            home_form=home_form,
            away_form=away_form,
            home_rating=team_ratings.get(home_team, 0.5),
            away_rating=team_ratings.get(away_team, 0.5),
            top_scorelines=[(str(s), p) for s, p in top],
        )

        has_llm = bool(llm_verdict.summary)
        llm_insight = llm_verdict.summary if has_llm else None

        prediction = FullPrediction(
            fixture_api_id=fixture.api_id,
            home_team=home_team,
            away_team=away_team,
            home_team_id=fixture.home_team_id,
            away_team_id=fixture.away_team_id,
            date=fixture.date,
            predicted_score=predicted_score,
            score_probability=score_prob,
            top_scorelines=[(str(s), round(p, 4)) for s, p in top],
            market=market,
            corners=corners,
            cards=cards,
            llm_verdict=llm_verdict if has_llm else None,
            llm_insight=llm_insight,
            llm_adjustment_applied=has_llm,
        )

        self._save_prediction(prediction)

        logger.info(
            f"Prediction: {home_team} {predicted_score} {away_team} | "
            f"{market.recommended_market} | "
            f"{market.home_recommended} | {market.away_recommended} | "
            f"Corners: {corners.recommended_pick} | "
            f"Cards: {cards.recommended_pick}"
        )

        return prediction

    def _predict_corners(
        self,
        fixture: Fixture,
        home_form: float,
        away_form: float,
        team_ratings: dict[str, float],
    ) -> CornerPrediction:
        """Build corner profiles and predict corners."""
        all_stats = self.db.query(FixtureStatistics).all()
        home_fixtures = self.data_service.get_team_fixtures(fixture.home_team_name)
        away_fixtures = self.data_service.get_team_fixtures(fixture.away_team_name)

        home_profile = self.corner_stats_calc.compute_corner_profile(
            fixture.home_team_id, fixture.home_team_name, home_fixtures, all_stats
        )
        away_profile = self.corner_stats_calc.compute_corner_profile(
            fixture.away_team_id, fixture.away_team_name, away_fixtures, all_stats
        )

        return self.corner_predictor.predict(
            home_profile, away_profile,
            home_form, away_form,
            team_ratings.get(fixture.home_team_name, 0.5),
            team_ratings.get(fixture.away_team_name, 0.5),
        )

    def _predict_cards(
        self,
        fixture: Fixture,
        home_form: float,
        away_form: float,
        team_ratings: dict[str, float],
    ) -> CardPrediction:
        """Build card profiles and predict yellow cards."""
        all_stats = self.db.query(FixtureStatistics).all()
        home_fixtures = self.data_service.get_team_fixtures(fixture.home_team_name)
        away_fixtures = self.data_service.get_team_fixtures(fixture.away_team_name)

        home_profile = self.card_stats_calc.compute_card_profile(
            fixture.home_team_id, fixture.home_team_name, home_fixtures, all_stats
        )
        away_profile = self.card_stats_calc.compute_card_profile(
            fixture.away_team_id, fixture.away_team_name, away_fixtures, all_stats
        )

        return self.card_predictor.predict(
            home_profile, away_profile,
            home_form, away_form,
            team_ratings.get(fixture.home_team_name, 0.5),
            team_ratings.get(fixture.away_team_name, 0.5),
        )

    def _save_prediction(self, pred: FullPrediction):
        """Save prediction to the database for accuracy tracking."""
        existing = (
            self.db.query(Prediction)
            .filter(Prediction.fixture_api_id == pred.fixture_api_id)
            .first()
        )
        if existing:
            self.db.delete(existing)

        # Build LLM insight text combining all reasoning
        llm_text = None
        if pred.llm_verdict and pred.llm_verdict.summary:
            v = pred.llm_verdict
            parts = [v.summary]
            if v.match_goals_reasoning:
                parts.append(f"Goals: {v.match_goals_pick} - {v.match_goals_reasoning}")
            if v.home_goals_reasoning:
                parts.append(f"Home: {v.home_goals_pick} - {v.home_goals_reasoning}")
            if v.away_goals_reasoning:
                parts.append(f"Away: {v.away_goals_pick} - {v.away_goals_reasoning}")
            if v.btts_reasoning:
                parts.append(f"BTTS: {v.btts_pick} - {v.btts_reasoning}")
            if v.corners_reasoning:
                parts.append(f"Corners: {v.corners_pick} - {v.corners_reasoning}")
            if v.cards_reasoning:
                parts.append(f"Cards: {v.cards_pick} - {v.cards_reasoning}")
            llm_text = " | ".join(parts)

        self.db.add(Prediction(
            fixture_api_id=pred.fixture_api_id,
            home_team_name=pred.home_team,
            away_team_name=pred.away_team,
            match_date=pred.date,
            predicted_home_goals=pred.predicted_score.home_goals,
            predicted_away_goals=pred.predicted_score.away_goals,
            score_probability=pred.score_probability,
            over_15_prob=pred.market.over_15,
            over_25_prob=pred.market.over_25,
            over_35_prob=pred.market.over_35,
            recommended_market=pred.market.recommended_market,
            market_confidence=pred.market.recommended_confidence,
            home_over_05_prob=pred.market.home_over_05,
            home_over_15_prob=pred.market.home_over_15,
            away_over_05_prob=pred.market.away_over_05,
            away_over_15_prob=pred.market.away_over_15,
            home_recommended_market=pred.market.home_recommended,
            home_market_confidence=pred.market.home_recommended_confidence,
            away_recommended_market=pred.market.away_recommended,
            away_market_confidence=pred.market.away_recommended_confidence,
            btts_yes_prob=pred.market.btts_yes,
            btts_pick=pred.market.btts_recommendation == "BTTS Yes",
            btts_confidence=pred.market.btts_confidence,
            predicted_total_corners=pred.corners.predicted_total,
            predicted_home_corners=pred.corners.home_corners,
            predicted_away_corners=pred.corners.away_corners,
            corner_recommended_line=pred.corners.recommended_line,
            corner_recommended_pick=pred.corners.recommended_pick,
            corner_confidence=pred.corners.confidence,
            predicted_total_cards=pred.cards.predicted_total,
            predicted_home_cards=pred.cards.home_cards,
            predicted_away_cards=pred.cards.away_cards,
            card_recommended_line=pred.cards.recommended_line,
            card_recommended_pick=pred.cards.recommended_pick,
            card_confidence=pred.cards.confidence,
            llm_insight=llm_text,
            llm_adjustment_applied=pred.llm_adjustment_applied,
        ))
        self.db.commit()

    async def predict_upcoming(self) -> list[FullPrediction]:
        """Generate predictions for all upcoming fixtures."""
        upcoming = self.data_service.get_upcoming_fixtures()
        predictions = []
        for fixture in upcoming:
            try:
                pred = await self.predict_fixture(fixture)
                predictions.append(pred)
            except Exception as e:
                logger.error(f"Failed to predict {fixture.home_team_name} vs {fixture.away_team_name}: {e}")
        return predictions

    def compute_accuracy(self) -> dict:
        """Compute accuracy metrics across all stored predictions with actual results."""
        predictions = (
            self.db.query(Prediction)
            .filter(Prediction.actual_home_goals.isnot(None))
            .all()
        )

        if not predictions:
            return {"total_predictions": 0, "message": "No completed predictions yet"}

        total = len(predictions)
        exact_score = 0
        correct_result = 0
        over_under_correct = 0
        btts_correct = 0
        corner_line_correct = 0
        card_line_correct = 0

        for p in predictions:
            actual_h = p.actual_home_goals
            actual_a = p.actual_away_goals
            actual_total = actual_h + actual_a

            if p.predicted_home_goals == actual_h and p.predicted_away_goals == actual_a:
                exact_score += 1

            pred_result = "H" if p.predicted_home_goals > p.predicted_away_goals else ("A" if p.predicted_away_goals > p.predicted_home_goals else "D")
            actual_result = "H" if actual_h > actual_a else ("A" if actual_a > actual_h else "D")
            if pred_result == actual_result:
                correct_result += 1

            market = p.recommended_market
            if "Over" in market:
                line = float(market.split()[-2])
                if actual_total > line:
                    over_under_correct += 1
            elif "Under" in market:
                line = float(market.split()[-2])
                if actual_total < line:
                    over_under_correct += 1

            actual_btts = actual_h > 0 and actual_a > 0
            if p.btts_pick == actual_btts:
                btts_correct += 1

            if p.actual_total_corners is not None and p.corner_recommended_line:
                is_over = "Over" in (p.corner_recommended_pick or "")
                if is_over and p.actual_total_corners > p.corner_recommended_line:
                    corner_line_correct += 1
                elif not is_over and p.actual_total_corners < p.corner_recommended_line:
                    corner_line_correct += 1

            if p.actual_total_cards is not None and p.card_recommended_line:
                is_over = "Over" in (p.card_recommended_pick or "")
                if is_over and p.actual_total_cards > p.card_recommended_line:
                    card_line_correct += 1
                elif not is_over and p.actual_total_cards < p.card_recommended_line:
                    card_line_correct += 1

        return {
            "total_predictions": total,
            "exact_score_accuracy": round(exact_score / total * 100, 1),
            "result_accuracy": round(correct_result / total * 100, 1),
            "over_under_accuracy": round(over_under_correct / total * 100, 1),
            "btts_accuracy": round(btts_correct / total * 100, 1),
            "corner_line_accuracy": round(corner_line_correct / total * 100, 1) if any(p.actual_total_corners is not None for p in predictions) else None,
            "card_line_accuracy": round(card_line_correct / total * 100, 1) if any(p.actual_total_cards is not None for p in predictions) else None,
        }

    async def update_actuals(self):
        """Update prediction records with actual results from completed fixtures."""
        predictions = (
            self.db.query(Prediction)
            .filter(Prediction.actual_home_goals.is_(None))
            .all()
        )

        for pred in predictions:
            fixture = (
                self.db.query(Fixture)
                .filter(Fixture.api_id == pred.fixture_api_id, Fixture.status == "FT")
                .first()
            )
            if fixture and fixture.home_goals is not None:
                pred.actual_home_goals = fixture.home_goals
                pred.actual_away_goals = fixture.away_goals

                corner_stats = (
                    self.db.query(FixtureStatistics)
                    .filter(FixtureStatistics.fixture_api_id == fixture.api_id)
                    .all()
                )
                if corner_stats:
                    total_corners = sum(
                        s.corners for s in corner_stats if s.corners is not None
                    )
                    pred.actual_total_corners = total_corners

                    total_cards = sum(
                        s.yellow_cards for s in corner_stats if s.yellow_cards is not None
                    )
                    pred.actual_total_cards = total_cards

        self.db.commit()

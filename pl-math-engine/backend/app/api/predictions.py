"""Prediction API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.prediction import Prediction as PredictionModel
from app.prediction_engine.prediction_service import PredictionService
from app.schemas.prediction import AccuracyResponse, PredictionResponse, RefreshResponse, ScorelineSchema, MarketSchema, CornerSchema, CardSchema, LLMVerdictSchema

router = APIRouter(prefix="/predictions", tags=["predictions"])


def _to_response(pred) -> PredictionResponse:
    return PredictionResponse(
        fixture_id=pred.fixture_api_id,
        home_team=pred.home_team,
        away_team=pred.away_team,
        home_team_id=pred.home_team_id,
        away_team_id=pred.away_team_id,
        date=pred.date,
        predicted_score=ScorelineSchema(
            home_goals=pred.predicted_score.home_goals,
            away_goals=pred.predicted_score.away_goals,
            total_goals=pred.predicted_score.total_goals,
            result=pred.predicted_score.result,
        ),
        score_probability=round(pred.score_probability, 4),
        top_scorelines=pred.top_scorelines,
        market=MarketSchema(
            over_05=pred.market.over_05,
            over_15=pred.market.over_15,
            over_25=pred.market.over_25,
            over_35=pred.market.over_35,
            home_over_05=pred.market.home_over_05,
            home_over_15=pred.market.home_over_15,
            home_over_25=pred.market.home_over_25,
            away_over_05=pred.market.away_over_05,
            away_over_15=pred.market.away_over_15,
            away_over_25=pred.market.away_over_25,
            btts_yes=pred.market.btts_yes,
            btts_no=pred.market.btts_no,
            recommended_market=pred.market.recommended_market,
            recommended_confidence=pred.market.recommended_confidence,
            btts_recommendation=pred.market.btts_recommendation,
            btts_confidence=pred.market.btts_confidence,
            home_recommended=pred.market.home_recommended,
            home_recommended_confidence=pred.market.home_recommended_confidence,
            away_recommended=pred.market.away_recommended,
            away_recommended_confidence=pred.market.away_recommended_confidence,
        ),
        corners=CornerSchema(
            predicted_total=pred.corners.predicted_total,
            home_corners=pred.corners.home_corners,
            away_corners=pred.corners.away_corners,
            over_85=pred.corners.over_85,
            over_95=pred.corners.over_95,
            over_105=pred.corners.over_105,
            over_115=pred.corners.over_115,
            recommended_line=pred.corners.recommended_line,
            recommended_pick=pred.corners.recommended_pick,
            confidence=pred.corners.confidence,
        ),
        cards=CardSchema(
            predicted_total=pred.cards.predicted_total,
            home_cards=pred.cards.home_cards,
            away_cards=pred.cards.away_cards,
            over_25=pred.cards.over_25,
            over_35=pred.cards.over_35,
            over_45=pred.cards.over_45,
            over_55=pred.cards.over_55,
            recommended_line=pred.cards.recommended_line,
            recommended_pick=pred.cards.recommended_pick,
            confidence=pred.cards.confidence,
        ),
        llm_verdict=LLMVerdictSchema(
            match_goals_pick=pred.llm_verdict.match_goals_pick,
            match_goals_confidence=pred.llm_verdict.match_goals_confidence,
            match_goals_reasoning=pred.llm_verdict.match_goals_reasoning,
            home_goals_pick=pred.llm_verdict.home_goals_pick,
            home_goals_reasoning=pred.llm_verdict.home_goals_reasoning,
            away_goals_pick=pred.llm_verdict.away_goals_pick,
            away_goals_reasoning=pred.llm_verdict.away_goals_reasoning,
            btts_pick=pred.llm_verdict.btts_pick,
            btts_confidence=pred.llm_verdict.btts_confidence,
            btts_reasoning=pred.llm_verdict.btts_reasoning,
            corners_pick=pred.llm_verdict.corners_pick,
            corners_confidence=pred.llm_verdict.corners_confidence,
            corners_reasoning=pred.llm_verdict.corners_reasoning,
            cards_pick=pred.llm_verdict.cards_pick,
            cards_confidence=pred.llm_verdict.cards_confidence,
            cards_reasoning=pred.llm_verdict.cards_reasoning,
            summary=pred.llm_verdict.summary,
        ) if pred.llm_verdict else None,
        llm_insight=pred.llm_insight,
        llm_adjustment_applied=pred.llm_adjustment_applied,
    )


@router.get("/upcoming", response_model=list[PredictionResponse])
async def get_upcoming_predictions(db: Session = Depends(get_db)):
    """Return predictions for all upcoming fixtures."""
    service = PredictionService(db)
    predictions = await service.predict_upcoming()
    return [_to_response(p) for p in predictions]


@router.get("/last-refreshed")
async def get_last_refreshed(db: Session = Depends(get_db)):
    """Return the timestamp of the most recent prediction."""
    latest = db.query(func.max(PredictionModel.created_at)).scalar()
    return {"last_refreshed": latest.isoformat() if latest else None}


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_predictions(db: Session = Depends(get_db)):
    """Trigger data refresh and recalculate all predictions."""
    service = PredictionService(db)

    # Refresh data from API-Football
    await service.data_service.refresh_all()

    # Update actuals for completed matches
    await service.update_actuals()

    # Generate new predictions
    predictions = await service.predict_upcoming()

    return RefreshResponse(
        status="success",
        message=f"Refreshed data and generated {len(predictions)} predictions",
    )


@router.get("/accuracy", response_model=AccuracyResponse)
async def get_accuracy(db: Session = Depends(get_db)):
    """Return accuracy metrics for past predictions."""
    service = PredictionService(db)
    accuracy = service.compute_accuracy()
    return AccuracyResponse(**accuracy)

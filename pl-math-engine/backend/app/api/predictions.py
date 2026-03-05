"""Prediction API endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.fixture import Fixture
from app.models.prediction import Prediction as PredictionModel
from app.prediction_engine.prediction_service import PredictionService
from app.schemas.dashboard import GameOfTheWeekItem, GameOfTheWeekResponse, MarketPick
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


def _get_result(home: int, away: int) -> str:
    if home > away:
        return "H"
    elif away > home:
        return "A"
    return "D"


def _check_ou(market: str, total: int) -> bool | None:
    for line in ["3.5", "2.5", "1.5", "0.5"]:
        t = float(line)
        if f"Over {line}" in market:
            return total > t
        if f"Under {line}" in market:
            return total < t
    return None


def _check_team_ou(market: str, goals: int) -> bool | None:
    for line in ["2.5", "1.5", "0.5"]:
        t = float(line)
        if f"Over {line}" in market:
            return goals > t
        if f"Under {line}" in market:
            return goals < t
    return None


def _best_pick_for_pred(pred) -> tuple[str, float] | None:
    """Find the single highest-confidence market pick for a prediction."""
    picks = []
    if pred.market_confidence:
        picks.append((pred.recommended_market, pred.market_confidence))
    if pred.btts_confidence:
        label = "BTTS Yes" if pred.btts_pick else "BTTS No"
        picks.append((label, pred.btts_confidence))
    if pred.home_market_confidence:
        picks.append((pred.home_recommended_market, pred.home_market_confidence))
    if pred.away_market_confidence:
        picks.append((pred.away_recommended_market, pred.away_market_confidence))
    if pred.corner_confidence:
        picks.append((f"{pred.corner_recommended_pick} {pred.corner_recommended_line} Corners", pred.corner_confidence))
    if pred.card_confidence:
        picks.append((f"{pred.card_recommended_pick} {pred.card_recommended_line} Cards", pred.card_confidence))
    if not picks:
        return None
    return max(picks, key=lambda x: x[1])


def _evaluate_pick(label: str, pred, actual_home: int, actual_away: int) -> bool | None:
    """Check if a best pick was correct given actual results."""
    actual_total = actual_home + actual_away
    if "BTTS" in label:
        btts_actual = actual_home >= 1 and actual_away >= 1
        return btts_actual if "Yes" in label else not btts_actual
    elif "Home" in label:
        return _check_team_ou(label, actual_home)
    elif "Away" in label:
        return _check_team_ou(label, actual_away)
    elif "Corners" in label:
        if pred.actual_total_corners is not None:
            return _check_ou(label.replace(" Corners", ""), pred.actual_total_corners)
        return None
    elif "Cards" in label:
        if pred.actual_total_cards is not None:
            return _check_ou(label.replace(" Cards", ""), pred.actual_total_cards)
        return None
    else:
        return _check_ou(label, actual_total)


@router.get("/game-of-the-week", response_model=GameOfTheWeekResponse | None)
async def get_game_of_the_week(db: Session = Depends(get_db)):
    """Return all games of the week with the best pick for each game.

    For every prediction in the current gameweek, picks the single
    highest-confidence market and checks if it was correct (for finished matches).
    """
    one_week_ago = datetime.utcnow() - timedelta(days=3)
    one_week_ahead = datetime.utcnow() + timedelta(days=7)

    predictions = (
        db.query(PredictionModel)
        .filter(
            PredictionModel.match_date >= one_week_ago,
            PredictionModel.match_date <= one_week_ahead,
        )
        .order_by(PredictionModel.match_date.asc())
        .all()
    )

    if not predictions:
        return None

    # Load fixtures for matchday info
    fixture_ids = [p.fixture_api_id for p in predictions]
    fixtures = db.query(Fixture).filter(Fixture.api_id.in_(fixture_ids)).all()
    fix_map = {f.api_id: f for f in fixtures}

    games: list[GameOfTheWeekItem] = []
    finished_count = 0
    correct_count = 0

    for pred in predictions:
        best = _best_pick_for_pred(pred)
        if not best:
            continue

        label, confidence = best
        fixture = fix_map.get(pred.fixture_api_id)

        is_finished = False
        actual_home = None
        actual_away = None
        pick_correct = None

        if pred.actual_home_goals is not None:
            is_finished = True
            actual_home = pred.actual_home_goals
            actual_away = pred.actual_away_goals
            pick_correct = _evaluate_pick(label, pred, actual_home, actual_away)
            finished_count += 1
            if pick_correct:
                correct_count += 1
        elif fixture and fixture.status == "FT" and fixture.home_goals is not None:
            is_finished = True
            actual_home = fixture.home_goals
            actual_away = fixture.away_goals
            pick_correct = _evaluate_pick(label, pred, actual_home, actual_away)
            finished_count += 1
            if pick_correct:
                correct_count += 1

        games.append(GameOfTheWeekItem(
            fixture_api_id=pred.fixture_api_id,
            home_team=pred.home_team_name,
            away_team=pred.away_team_name,
            date=pred.match_date,
            matchday=fixture.matchday if fixture else None,
            predicted_home_goals=pred.predicted_home_goals,
            predicted_away_goals=pred.predicted_away_goals,
            best_pick_label=label,
            best_pick_confidence=round(confidence, 4),
            actual_home_goals=actual_home,
            actual_away_goals=actual_away,
            is_finished=is_finished,
            pick_correct=pick_correct,
        ))

    return GameOfTheWeekResponse(
        games=games,
        total_games=len(games),
        finished_games=finished_count,
        correct_picks=correct_count,
        accuracy=round(correct_count / finished_count * 100, 1) if finished_count > 0 else None,
    )

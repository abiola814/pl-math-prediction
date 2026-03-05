"""Results API endpoints — completed matches with prediction comparison."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.schemas.dashboard import ResultWithPrediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["results"])


def _get_result(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    elif away_goals > home_goals:
        return "A"
    return "D"


@router.get("/", response_model=list[ResultWithPrediction])
async def get_results(limit: int = 20, db: Session = Depends(get_db)):
    """Return recent completed fixtures with their predictions."""
    fixtures = (
        db.query(Fixture)
        .filter(Fixture.status == "FT", Fixture.season == settings.CURRENT_SEASON)
        .order_by(Fixture.date.desc())
        .limit(limit)
        .all()
    )

    # Batch-load predictions for these fixtures
    fixture_ids = [f.api_id for f in fixtures]
    predictions = (
        db.query(Prediction)
        .filter(Prediction.fixture_api_id.in_(fixture_ids))
        .all()
    )
    pred_map = {p.fixture_api_id: p for p in predictions}

    result = []
    for fix in fixtures:
        actual_home = fix.home_goals or 0
        actual_away = fix.away_goals or 0
        actual_result = _get_result(actual_home, actual_away)

        pred = pred_map.get(fix.api_id)

        predicted_home = pred.predicted_home_goals if pred else None
        predicted_away = pred.predicted_away_goals if pred else None
        predicted_result = None
        score_correct = False
        result_correct = False
        recommended_market = None
        market_correct = None

        if pred:
            predicted_result = _get_result(pred.predicted_home_goals, pred.predicted_away_goals)
            score_correct = (
                pred.predicted_home_goals == actual_home
                and pred.predicted_away_goals == actual_away
            )
            result_correct = predicted_result == actual_result
            recommended_market = pred.recommended_market

            # Check if market recommendation was correct
            if recommended_market:
                actual_total = actual_home + actual_away
                if "Over 3.5" in recommended_market:
                    market_correct = actual_total > 3.5
                elif "Under 3.5" in recommended_market:
                    market_correct = actual_total < 3.5
                elif "Over 2.5" in recommended_market:
                    market_correct = actual_total > 2.5
                elif "Under 2.5" in recommended_market:
                    market_correct = actual_total < 2.5
                elif "Over 1.5" in recommended_market:
                    market_correct = actual_total > 1.5
                elif "Under 1.5" in recommended_market:
                    market_correct = actual_total < 1.5
                elif "Over 0.5" in recommended_market:
                    market_correct = actual_total > 0.5
                elif "Under 0.5" in recommended_market:
                    market_correct = actual_total < 0.5

        result.append(ResultWithPrediction(
            fixture_api_id=fix.api_id,
            home_team=fix.home_team_name,
            away_team=fix.away_team_name,
            date=fix.date,
            matchday=fix.matchday,
            actual_home_goals=actual_home,
            actual_away_goals=actual_away,
            predicted_home_goals=predicted_home,
            predicted_away_goals=predicted_away,
            predicted_result=predicted_result,
            actual_result=actual_result,
            score_correct=score_correct,
            result_correct=result_correct,
            recommended_market=recommended_market,
            market_correct=market_correct,
        ))

    return result

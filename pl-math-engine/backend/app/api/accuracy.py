"""Accuracy tracking API endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import AccuracyResponse

router = APIRouter(prefix="/accuracy", tags=["accuracy"])


@router.get("/", response_model=AccuracyResponse)
async def get_accuracy(db: Session = Depends(get_db)):
    """Return accuracy metrics for all predictions with actual results."""
    predictions = (
        db.query(Prediction)
        .filter(Prediction.actual_home_goals.isnot(None))
        .all()
    )

    if not predictions:
        return AccuracyResponse(
            total_predictions=0,
            message="No completed predictions yet",
        )

    total = len(predictions)
    exact = 0
    result_correct = 0
    ou_correct = 0
    btts_correct = 0
    corner_correct = 0
    corner_total = 0

    for p in predictions:
        ah, aa = p.actual_home_goals, p.actual_away_goals
        ph, pa = p.predicted_home_goals, p.predicted_away_goals

        if ph == ah and pa == aa:
            exact += 1

        pred_r = "H" if ph > pa else ("A" if pa > ph else "D")
        actual_r = "H" if ah > aa else ("A" if aa > ah else "D")
        if pred_r == actual_r:
            result_correct += 1

        actual_total = ah + aa
        market = p.recommended_market
        if "Over" in market:
            line = float(market.split()[-2])
            if actual_total > line:
                ou_correct += 1
        elif "Under" in market:
            line = float(market.split()[-2])
            if actual_total < line:
                ou_correct += 1

        actual_btts = ah > 0 and aa > 0
        if p.btts_pick == actual_btts:
            btts_correct += 1

        if p.actual_total_corners is not None and p.corner_recommended_line:
            corner_total += 1
            is_over = "Over" in (p.corner_recommended_pick or "")
            if is_over and p.actual_total_corners > p.corner_recommended_line:
                corner_correct += 1
            elif not is_over and p.actual_total_corners < p.corner_recommended_line:
                corner_correct += 1

    return AccuracyResponse(
        total_predictions=total,
        exact_score_accuracy=round(exact / total * 100, 1),
        result_accuracy=round(result_correct / total * 100, 1),
        over_under_accuracy=round(ou_correct / total * 100, 1),
        btts_accuracy=round(btts_correct / total * 100, 1),
        corner_line_accuracy=round(corner_correct / corner_total * 100, 1) if corner_total else None,
    )

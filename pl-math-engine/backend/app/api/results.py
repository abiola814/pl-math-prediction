"""Results API endpoints — completed matches with prediction comparison."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.fixture import Fixture
from app.models.prediction import Prediction
from app.schemas.dashboard import MarketPick, ResultWithPrediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["results"])


def _get_result(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    elif away_goals > home_goals:
        return "A"
    return "D"


def _check_over_under(market: str, actual_total: int) -> bool | None:
    """Check if an Over/Under market pick was correct."""
    for line in ["3.5", "2.5", "1.5", "0.5"]:
        threshold = float(line)
        if f"Over {line}" in market:
            return actual_total > threshold
        if f"Under {line}" in market:
            return actual_total < threshold
    return None


def _check_team_over_under(market: str, team_goals: int) -> bool | None:
    """Check if a team-level Over/Under pick was correct."""
    for line in ["2.5", "1.5", "0.5"]:
        threshold = float(line)
        if f"Over {line}" in market:
            return team_goals > threshold
        if f"Under {line}" in market:
            return team_goals < threshold
    return None


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

        markets: list[MarketPick] = []

        if pred:
            predicted_result = _get_result(pred.predicted_home_goals, pred.predicted_away_goals)
            score_correct = (
                pred.predicted_home_goals == actual_home
                and pred.predicted_away_goals == actual_away
            )
            result_correct = predicted_result == actual_result
            recommended_market = pred.recommended_market
            actual_total = actual_home + actual_away

            # Check if main market recommendation was correct
            if recommended_market:
                market_correct = _check_over_under(recommended_market, actual_total)

            # Build all market picks with confidence, then take top 3
            all_picks: list[MarketPick] = []

            # 1) Match goals
            all_picks.append(MarketPick(
                label=pred.recommended_market,
                confidence=pred.market_confidence or 0,
                correct=_check_over_under(pred.recommended_market, actual_total),
            ))

            # 2) BTTS
            btts_label = "BTTS Yes" if pred.btts_pick else "BTTS No"
            btts_actual = actual_home >= 1 and actual_away >= 1
            all_picks.append(MarketPick(
                label=btts_label,
                confidence=pred.btts_confidence or 0,
                correct=(btts_actual if pred.btts_pick else not btts_actual),
            ))

            # 3) Home team goals
            if pred.home_recommended_market:
                all_picks.append(MarketPick(
                    label=pred.home_recommended_market,
                    confidence=pred.home_market_confidence or 0,
                    correct=_check_team_over_under(pred.home_recommended_market, actual_home),
                ))

            # 4) Away team goals
            if pred.away_recommended_market:
                all_picks.append(MarketPick(
                    label=pred.away_recommended_market,
                    confidence=pred.away_market_confidence or 0,
                    correct=_check_team_over_under(pred.away_recommended_market, actual_away),
                ))

            # 5) Corners
            if pred.corner_recommended_pick:
                corner_label = f"{pred.corner_recommended_pick} {pred.corner_recommended_line} Corners"
                corner_correct = None
                if pred.actual_total_corners is not None:
                    if "Over" in pred.corner_recommended_pick:
                        corner_correct = pred.actual_total_corners > pred.corner_recommended_line
                    else:
                        corner_correct = pred.actual_total_corners < pred.corner_recommended_line
                all_picks.append(MarketPick(
                    label=corner_label,
                    confidence=pred.corner_confidence or 0,
                    correct=corner_correct,
                ))

            # 6) Cards
            if pred.card_recommended_pick:
                card_label = f"{pred.card_recommended_pick} {pred.card_recommended_line} Cards"
                card_correct = None
                if pred.actual_total_cards is not None:
                    if "Over" in pred.card_recommended_pick:
                        card_correct = pred.actual_total_cards > pred.card_recommended_line
                    else:
                        card_correct = pred.actual_total_cards < pred.card_recommended_line
                all_picks.append(MarketPick(
                    label=card_label,
                    confidence=pred.card_confidence or 0,
                    correct=card_correct,
                ))

            # Sort by confidence and take top 3
            all_picks.sort(key=lambda m: m.confidence, reverse=True)
            markets = all_picks[:3]

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
            markets=markets,
        ))

    return result

"""Fixture API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.data.data_service import DataService
from app.schemas.prediction import FixtureResponse

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


def _fixture_to_response(fix) -> FixtureResponse:
    return FixtureResponse(
        api_id=fix.api_id,
        home_team=fix.home_team_name,
        away_team=fix.away_team_name,
        home_team_id=fix.home_team_id,
        away_team_id=fix.away_team_id,
        date=fix.date,
        status=fix.status,
        home_goals=fix.home_goals,
        away_goals=fix.away_goals,
        matchday=fix.matchday,
        season=fix.season,
    )


@router.get("/upcoming", response_model=list[FixtureResponse])
async def get_upcoming_fixtures(db: Session = Depends(get_db)):
    """Return upcoming fixtures."""
    service = DataService(db)
    fixtures = service.get_upcoming_fixtures()
    return [_fixture_to_response(f) for f in fixtures]


@router.get("/results", response_model=list[FixtureResponse])
async def get_recent_results(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Return recent completed fixtures."""
    service = DataService(db)
    fixtures = service.get_finished_fixtures(settings.CURRENT_SEASON)
    return [_fixture_to_response(f) for f in fixtures[-limit:]]

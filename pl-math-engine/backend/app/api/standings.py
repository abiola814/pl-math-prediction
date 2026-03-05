"""Standings API endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.data.data_service import DataService
from app.data.form_calculator import FormCalculator
from app.data.home_advantages import HomeAdvantageCalculator
from app.data.team_ratings import TeamRatingCalculator
from app.database import get_db
from app.models.team import Team
from app.schemas.dashboard import StandingOverviewItem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/standings", tags=["standings"])


@router.get("/overview", response_model=list[StandingOverviewItem])
async def get_standings_overview(db: Session = Depends(get_db)):
    """Return league standings enriched with ratings, form, and home advantage."""
    service = DataService(db)

    # Get standings across seasons
    standings_by_season = service.get_standings_multi_season()
    current_standings = standings_by_season.get(settings.CURRENT_SEASON, [])

    if not current_standings:
        return []

    # Compute team ratings
    team_ratings = TeamRatingCalculator().compute(
        standings_by_season, settings.CURRENT_SEASON
    )

    # Build fixtures by season for home advantage calculator
    fixtures_by_season = {}
    for offset in range(settings.NUM_SEASONS):
        season = settings.CURRENT_SEASON - offset
        fixtures_by_season[season] = service.get_finished_fixtures(season)

    home_advantages = HomeAdvantageCalculator().compute(
        fixtures_by_season, settings.CURRENT_SEASON
    )

    # Compute form for each team
    form_calc = FormCalculator()

    # Build team logo lookup
    all_teams = db.query(Team).all()
    logo_by_api_id = {t.api_id: t.logo_url for t in all_teams}

    result = []
    for s in current_standings:
        team_fixtures = service.get_team_fixtures(s.team_name)
        form_val = form_calc.calc_form(s.team_name, team_fixtures, team_ratings)

        result.append(StandingOverviewItem(
            position=s.position,
            team_name=s.team_name,
            team_api_id=s.team_api_id,
            logo_url=logo_by_api_id.get(s.team_api_id),
            played=s.played,
            won=s.won,
            drawn=s.drawn,
            lost=s.lost,
            goals_for=s.goals_for,
            goals_against=s.goals_against,
            goal_difference=s.goal_difference,
            points=s.points,
            home_won=s.home_won,
            home_drawn=s.home_drawn,
            home_lost=s.home_lost,
            away_won=s.away_won,
            away_drawn=s.away_drawn,
            away_lost=s.away_lost,
            rating=round(team_ratings.get(s.team_name, 0.0), 3),
            form=round(form_val, 3),
            home_advantage=round(home_advantages.get(s.team_name, 0.0), 3),
        ))

    return result

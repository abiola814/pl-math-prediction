"""Pydantic response schemas for dashboard pages."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.prediction import FixtureResponse


class StandingOverviewItem(BaseModel):
    position: int
    team_name: str
    team_api_id: int
    logo_url: Optional[str] = None
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    home_won: int
    home_drawn: int
    home_lost: int
    away_won: int
    away_drawn: int
    away_lost: int
    rating: float
    form: float
    home_advantage: float


class TeamFixtureResult(BaseModel):
    date: datetime
    opponent: str
    is_home: bool
    goals_for: int
    goals_against: int
    result: str  # "W", "D", "L"
    matchday: Optional[int] = None


class InjuryItem(BaseModel):
    player_name: str
    player_position: Optional[str] = None
    reason: Optional[str] = None


class GoalsAnalysis(BaseModel):
    avg_scored: float
    avg_conceded: float
    avg_scored_home: float
    avg_scored_away: float
    avg_conceded_home: float
    avg_conceded_away: float
    clean_sheets: int
    failed_to_score: int
    total_matches: int


class MiniTableRow(BaseModel):
    position: int
    team_name: str
    logo_url: Optional[str] = None
    goal_difference: int
    points: int
    is_current: bool = False


class OpponentInfo(BaseModel):
    name: str
    position: int
    form: float
    rating: float


class TeamDashboardResponse(BaseModel):
    team_name: str
    team_api_id: int
    logo_url: Optional[str] = None
    position: int
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    rating: float
    form: float
    home_advantage: float
    recent_form: list[TeamFixtureResult]
    season_fixtures: list[TeamFixtureResult]
    injuries: list[InjuryItem]
    goals_analysis: GoalsAnalysis
    next_fixture: Optional[FixtureResponse] = None
    next_opponent_info: Optional[OpponentInfo] = None
    h2h_vs_next: list[TeamFixtureResult]
    mini_table: list[MiniTableRow]


class FormHistoryPoint(BaseModel):
    matchday: int
    form: float
    cumulative_points: int
    goals_scored: int
    goals_conceded: int
    cumulative_goals_for: int
    cumulative_goals_against: int


class ResultWithPrediction(BaseModel):
    fixture_api_id: int
    home_team: str
    away_team: str
    date: datetime
    matchday: Optional[int] = None
    actual_home_goals: int
    actual_away_goals: int
    predicted_home_goals: Optional[int] = None
    predicted_away_goals: Optional[int] = None
    predicted_result: Optional[str] = None  # "H", "D", "A"
    actual_result: str
    score_correct: bool
    result_correct: bool
    recommended_market: Optional[str] = None
    market_correct: Optional[bool] = None


# ── Analysis Schemas ───────────────────────────────────────────

class TeamMatchdaySnapshot(BaseModel):
    """One team's data at a given matchday."""
    matchday: int
    form: float  # 0-1, rolling 5-match points %
    cumulative_points: int
    position: int


class AllTeamsTimeSeries(BaseModel):
    """Time series data for all 20 teams, for form/position/points over time charts."""
    teams: dict[str, list[TeamMatchdaySnapshot]]  # team_name -> list of snapshots


class GoalFrequency(BaseModel):
    """Goal frequency distribution for a team vs league average."""
    goals: list[int]                  # [0, 1, 2, 3, 4, 5+]
    team_scored_pct: list[float]      # percentage for each goal count (scored)
    team_conceded_pct: list[float]    # percentage for each goal count (conceded)
    avg_scored_pct: list[float]       # league average scored
    avg_conceded_pct: list[float]     # league average conceded


class ScorelineFrequencyItem(BaseModel):
    """A single scoreline and its frequencies."""
    scoreline: str        # e.g. "1-0", "2-1"
    team_pct: float       # this team's frequency %
    avg_pct: float        # league average frequency %
    outcome: str          # "W", "D", "L"


class SpiderAttribute(BaseModel):
    """One axis of the spider/radar chart."""
    name: str
    team_value: float   # 0-100 scaled
    avg_value: float    # 0-100 league average


class TeamComparisonData(BaseModel):
    """Spider/radar chart data for a team."""
    team_name: str
    attributes: list[SpiderAttribute]

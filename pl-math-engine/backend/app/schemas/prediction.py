"""Pydantic response schemas for the API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScorelineSchema(BaseModel):
    home_goals: int
    away_goals: int
    total_goals: int
    result: str  # "H", "D", "A"


class MarketSchema(BaseModel):
    over_05: float
    over_15: float
    over_25: float
    over_35: float
    home_over_05: float
    home_over_15: float
    home_over_25: float
    away_over_05: float
    away_over_15: float
    away_over_25: float
    btts_yes: float
    btts_no: float
    recommended_market: str
    recommended_confidence: float
    btts_recommendation: str
    btts_confidence: float
    home_recommended: str
    home_recommended_confidence: float
    away_recommended: str
    away_recommended_confidence: float


class CornerSchema(BaseModel):
    predicted_total: float
    home_corners: float
    away_corners: float
    over_65: float
    over_85: float
    over_95: float
    over_105: float
    over_115: float
    recommended_line: float
    recommended_pick: str
    confidence: float


class CardSchema(BaseModel):
    predicted_total: float
    home_cards: float
    away_cards: float
    over_25: float
    over_35: float
    over_45: float
    over_55: float
    recommended_line: float
    recommended_pick: str
    confidence: float


class LLMVerdictSchema(BaseModel):
    match_goals_pick: str
    match_goals_confidence: int
    match_goals_reasoning: str
    home_goals_pick: str
    home_goals_reasoning: str
    away_goals_pick: str
    away_goals_reasoning: str
    btts_pick: str
    btts_confidence: int
    btts_reasoning: str
    corners_pick: str
    corners_confidence: int
    corners_reasoning: str
    cards_pick: str
    cards_confidence: int
    cards_reasoning: str
    summary: str


class PredictionResponse(BaseModel):
    fixture_id: int
    home_team: str
    away_team: str
    home_team_id: int
    away_team_id: int
    date: datetime
    predicted_score: ScorelineSchema
    score_probability: float
    top_scorelines: list[tuple[str, float]]
    market: MarketSchema
    corners: CornerSchema
    cards: CardSchema
    llm_verdict: Optional[LLMVerdictSchema] = None
    llm_insight: Optional[str] = None
    llm_adjustment_applied: bool = False


class AccuracyResponse(BaseModel):
    total_predictions: int
    exact_score_accuracy: Optional[float] = None
    result_accuracy: Optional[float] = None
    over_under_accuracy: Optional[float] = None
    btts_accuracy: Optional[float] = None
    corner_line_accuracy: Optional[float] = None
    card_line_accuracy: Optional[float] = None
    best_pick_accuracy: Optional[float] = None
    message: Optional[str] = None


class FixtureResponse(BaseModel):
    api_id: int
    home_team: str
    away_team: str
    home_team_id: int
    away_team_id: int
    date: datetime
    status: str
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    matchday: Optional[int] = None
    season: int


class RefreshResponse(BaseModel):
    status: str
    message: str

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_api_id: Mapped[int] = mapped_column(Integer, index=True)
    home_team_name: Mapped[str] = mapped_column(String(100))
    away_team_name: Mapped[str] = mapped_column(String(100))
    match_date: Mapped[datetime] = mapped_column(DateTime)

    # Score prediction
    predicted_home_goals: Mapped[int] = mapped_column(Integer)
    predicted_away_goals: Mapped[int] = mapped_column(Integer)
    score_probability: Mapped[float] = mapped_column(Float)

    # Over/Under markets (match-level)
    over_15_prob: Mapped[float] = mapped_column(Float)
    over_25_prob: Mapped[float] = mapped_column(Float)
    over_35_prob: Mapped[float] = mapped_column(Float)
    recommended_market: Mapped[str] = mapped_column(String(50))
    market_confidence: Mapped[float] = mapped_column(Float)

    # Home/Away team Over/Under
    home_over_05_prob: Mapped[float] = mapped_column(Float, nullable=True)
    home_over_15_prob: Mapped[float] = mapped_column(Float, nullable=True)
    away_over_05_prob: Mapped[float] = mapped_column(Float, nullable=True)
    away_over_15_prob: Mapped[float] = mapped_column(Float, nullable=True)
    home_recommended_market: Mapped[str] = mapped_column(String(50), nullable=True)
    home_market_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    away_recommended_market: Mapped[str] = mapped_column(String(50), nullable=True)
    away_market_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # BTTS
    btts_yes_prob: Mapped[float] = mapped_column(Float)
    btts_pick: Mapped[bool] = mapped_column(Boolean)
    btts_confidence: Mapped[float] = mapped_column(Float)

    # Corners
    predicted_total_corners: Mapped[float] = mapped_column(Float, nullable=True)
    predicted_home_corners: Mapped[float] = mapped_column(Float, nullable=True)
    predicted_away_corners: Mapped[float] = mapped_column(Float, nullable=True)
    corner_recommended_line: Mapped[float] = mapped_column(Float, nullable=True)
    corner_recommended_pick: Mapped[str] = mapped_column(String(30), nullable=True)
    corner_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Cards (yellow)
    predicted_total_cards: Mapped[float] = mapped_column(Float, nullable=True)
    predicted_home_cards: Mapped[float] = mapped_column(Float, nullable=True)
    predicted_away_cards: Mapped[float] = mapped_column(Float, nullable=True)
    card_recommended_line: Mapped[float] = mapped_column(Float, nullable=True)
    card_recommended_pick: Mapped[str] = mapped_column(String(30), nullable=True)
    card_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # LLM
    llm_insight: Mapped[str] = mapped_column(Text, nullable=True)
    llm_adjustment_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    # Actual results (filled after match)
    actual_home_goals: Mapped[int] = mapped_column(Integer, nullable=True)
    actual_away_goals: Mapped[int] = mapped_column(Integer, nullable=True)
    actual_total_corners: Mapped[int] = mapped_column(Integer, nullable=True)
    actual_total_cards: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    home_team_id: Mapped[int] = mapped_column(Integer, index=True)
    away_team_id: Mapped[int] = mapped_column(Integer, index=True)
    home_team_name: Mapped[str] = mapped_column(String(100))
    away_team_name: Mapped[str] = mapped_column(String(100))
    date: Mapped[datetime] = mapped_column(DateTime)
    matchday: Mapped[int] = mapped_column(Integer, nullable=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    league_id: Mapped[int] = mapped_column(Integer, default=39)
    status: Mapped[str] = mapped_column(String(10), default="NS")
    home_goals: Mapped[int] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=True)

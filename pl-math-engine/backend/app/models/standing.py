from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Standing(Base):
    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_api_id: Mapped[int] = mapped_column(Integer, index=True)
    team_name: Mapped[str] = mapped_column(String(100))
    season: Mapped[int] = mapped_column(Integer, index=True)
    position: Mapped[int] = mapped_column(Integer)
    played: Mapped[int] = mapped_column(Integer)
    won: Mapped[int] = mapped_column(Integer)
    drawn: Mapped[int] = mapped_column(Integer)
    lost: Mapped[int] = mapped_column(Integer)
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
    goal_difference: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    home_won: Mapped[int] = mapped_column(Integer, default=0)
    home_drawn: Mapped[int] = mapped_column(Integer, default=0)
    home_lost: Mapped[int] = mapped_column(Integer, default=0)
    away_won: Mapped[int] = mapped_column(Integer, default=0)
    away_drawn: Mapped[int] = mapped_column(Integer, default=0)
    away_lost: Mapped[int] = mapped_column(Integer, default=0)

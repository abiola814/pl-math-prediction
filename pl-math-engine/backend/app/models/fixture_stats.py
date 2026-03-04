from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FixtureStatistics(Base):
    __tablename__ = "fixture_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_api_id: Mapped[int] = mapped_column(Integer, index=True)
    team_api_id: Mapped[int] = mapped_column(Integer, index=True)
    corners: Mapped[int] = mapped_column(Integer, nullable=True)
    shots_on_target: Mapped[int] = mapped_column(Integer, nullable=True)
    shots_total: Mapped[int] = mapped_column(Integer, nullable=True)
    possession: Mapped[float] = mapped_column(Float, nullable=True)
    fouls: Mapped[int] = mapped_column(Integer, nullable=True)
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=True)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=True)

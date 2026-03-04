from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Injury(Base):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_api_id: Mapped[int] = mapped_column(Integer, index=True)
    team_name: Mapped[str] = mapped_column(String(100))
    player_name: Mapped[str] = mapped_column(String(100))
    player_position: Mapped[str] = mapped_column(String(50), nullable=True)
    injury_type: Mapped[str] = mapped_column(String(100), nullable=True)
    reason: Mapped[str] = mapped_column(String(200), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

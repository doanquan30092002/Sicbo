from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base


class GameResultModel(Base):
    __tablename__ = "game_results"
    __table_args__ = (UniqueConstraint("game_id", "draw_date", name="uq_game_result_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    draw_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    parsed_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

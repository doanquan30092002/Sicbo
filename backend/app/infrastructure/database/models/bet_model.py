from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base


class BetModel(Base):
    __tablename__ = "bets"
    __table_args__ = (
        Index("ix_bets_game_date_status", "game_id", "draw_date", "status"),
        Index("ix_bets_user_date", "user_id", "draw_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    game_id: Mapped[str] = mapped_column(String(20), nullable=False)
    draw_date: Mapped[date] = mapped_column(Date, nullable=False)
    bet_type_id: Mapped[str] = mapped_column(String(20), nullable=False)
    numbers: Mapped[list] = mapped_column(JSONB, nullable=False)
    stake_per_point: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    points: Mapped[int] = mapped_column(nullable=False, default=1)
    total_stake: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    potential_win: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    win_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal(0))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

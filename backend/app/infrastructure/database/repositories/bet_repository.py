"""Concrete BetRepository — PostgreSQL via SQLAlchemy async."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.bet import Bet
from app.domain.repositories.bet_repo import IBetRepository
from app.domain.value_objects.bet_type import BetStatus
from app.infrastructure.database.models.bet_model import BetModel


def _to_entity(m: BetModel) -> Bet:
    return Bet(
        id=m.id,
        user_id=m.user_id,
        game_id=m.game_id,
        draw_date=m.draw_date,
        bet_type_id=m.bet_type_id,
        numbers=list(m.numbers),
        stake_per_point=m.stake_per_point,
        points=m.points,
        total_stake=m.total_stake,
        potential_win=m.potential_win,
        status=m.status,
        win_amount=m.win_amount,
        placed_at=m.placed_at,
        source=m.source,
        settled_at=m.settled_at,
    )


class BetRepository(IBetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        user_id: int,
        game_id: str,
        draw_date: date,
        bet_type_id: str,
        numbers: list[str],
        stake_per_point: Decimal,
        points: int,
        total_stake: Decimal,
        potential_win: Decimal,
        source: str = "web",
    ) -> Bet:
        m = BetModel(
            user_id=user_id,
            game_id=game_id,
            draw_date=draw_date,
            bet_type_id=bet_type_id,
            numbers=numbers,
            stake_per_point=stake_per_point,
            points=points,
            total_stake=total_stake,
            potential_win=potential_win,
            source=source,
            status=BetStatus.PENDING.value,
            win_amount=Decimal(0),
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def get_by_id(self, bet_id: int) -> Optional[Bet]:
        m = await self._session.get(BetModel, bet_id)
        return _to_entity(m) if m else None

    async def get_user_bets(
        self,
        user_id: int,
        game_id: Optional[str] = None,
        draw_date: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Bet], int]:
        conditions = [BetModel.user_id == user_id]
        if game_id:
            conditions.append(BetModel.game_id == game_id)
        if draw_date:
            conditions.append(BetModel.draw_date == draw_date)
        if status:
            conditions.append(BetModel.status == status)

        count_stmt = select(func.count(BetModel.id)).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(BetModel)
            .where(*conditions)
            .order_by(BetModel.placed_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in rows], total

    async def get_pending_bets_for_settlement(
        self, game_id: str, draw_date: date
    ) -> list[Bet]:
        stmt = select(BetModel).where(
            BetModel.game_id == game_id,
            BetModel.draw_date == draw_date,
            BetModel.status == BetStatus.PENDING.value,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in rows]

    async def update_status(
        self,
        bet_id: int,
        status: str,
        win_amount: Decimal,
    ) -> Bet:
        m = await self._session.get(BetModel, bet_id)
        if m is None:
            raise ValueError(f"Bet #{bet_id} không tồn tại.")
        m.status = status.value if hasattr(status, "value") else status
        m.win_amount = win_amount
        m.settled_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _to_entity(m)

    async def cancel(self, bet_id: int) -> Bet:
        m = await self._session.get(BetModel, bet_id)
        if m is None:
            raise ValueError(f"Bet #{bet_id} không tồn tại.")
        m.status = BetStatus.CANCELLED.value
        m.settled_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _to_entity(m)

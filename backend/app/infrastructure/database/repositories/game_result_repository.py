"""Concrete GameResultRepository — PostgreSQL via SQLAlchemy async."""
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.game_result import GameResult
from app.domain.repositories.game_result_repo import IGameResultRepository
from app.infrastructure.database.models.game_result_model import GameResultModel


def _to_entity(m: GameResultModel) -> GameResult:
    return GameResult(
        id=m.id,
        game_id=m.game_id,
        draw_date=m.draw_date,
        parsed_data=m.parsed_data,
        raw_json=m.raw_json,
        fetched_at=m.fetched_at,
    )


class GameResultRepository(IGameResultRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        game_id: str,
        draw_date: date,
        parsed_data: dict,
        raw_json: str,
    ) -> GameResult:
        m = GameResultModel(
            game_id=game_id,
            draw_date=draw_date,
            parsed_data=parsed_data,
            raw_json=raw_json,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def get_by_game_and_date(
        self, game_id: str, draw_date: date
    ) -> Optional[GameResult]:
        stmt = select(GameResultModel).where(
            GameResultModel.game_id == game_id,
            GameResultModel.draw_date == draw_date,
        )
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_recent(self, game_id: str, limit: int = 7) -> list[GameResult]:
        stmt = (
            select(GameResultModel)
            .where(GameResultModel.game_id == game_id)
            .order_by(GameResultModel.draw_date.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in rows]

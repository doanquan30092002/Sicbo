"""TelegramLinkTokenRepository — PostgreSQL via SQLAlchemy async."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.telegram_link_repo import (
    ITelegramLinkTokenRepository,
    TelegramLinkToken,
)
from app.infrastructure.database.models.telegram_link_token_model import (
    TelegramLinkTokenModel,
)


def _to_entity(m: TelegramLinkTokenModel) -> TelegramLinkToken:
    return TelegramLinkToken(
        id=m.id,
        user_id=m.user_id,
        token=m.token,
        expires_at=m.expires_at,
        used=m.used,
        created_at=m.created_at,
    )


class TelegramLinkTokenRepository(ITelegramLinkTokenRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, user_id: int, token: str, expires_at: datetime
    ) -> TelegramLinkToken:
        m = TelegramLinkTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def get_by_token(self, token: str) -> Optional[TelegramLinkToken]:
        stmt = select(TelegramLinkTokenModel).where(
            TelegramLinkTokenModel.token == token
        )
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(m) if m else None

    async def mark_used(self, token_id: int) -> None:
        m = await self._session.get(TelegramLinkTokenModel, token_id)
        if m is not None:
            m.used = True
            await self._session.flush()

    async def delete_expired(self) -> int:
        stmt = delete(TelegramLinkTokenModel).where(
            TelegramLinkTokenModel.expires_at < datetime.now(timezone.utc)
        )
        result = await self._session.execute(stmt)
        return result.rowcount or 0

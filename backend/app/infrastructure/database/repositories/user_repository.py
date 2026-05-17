"""Concrete UserRepository — PostgreSQL via SQLAlchemy async."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repo import IUserRepository
from app.infrastructure.database.models.user_model import UserModel


def _to_entity(m: UserModel) -> User:
    return User(
        id=m.id,
        username=m.username,
        password_hash=m.password_hash,
        balance=m.balance,
        is_active=m.is_active,
        is_admin=m.is_admin,
        created_at=m.created_at,
        updated_at=m.updated_at,
        phone=m.phone,
        email=m.email,
        telegram_id=m.telegram_id,
        telegram_username=m.telegram_username,
    )


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        username: str,
        password_hash: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        m = UserModel(
            username=username,
            password_hash=password_hash,
            phone=phone,
            email=email,
            balance=Decimal(0),
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        m = await self._session.get(UserModel, user_id)
        return _to_entity(m) if m else None

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username)
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(m) if m else None

    async def link_telegram(
        self, user_id: int, telegram_id: int, telegram_username: Optional[str]
    ) -> User:
        m = await self._session.get(UserModel, user_id)
        if m is None:
            raise ValueError(f"User #{user_id} không tồn tại.")
        m.telegram_id = telegram_id
        m.telegram_username = telegram_username
        await self._session.flush()
        return _to_entity(m)

    async def get_balance_for_update(self, user_id: int) -> Decimal:
        stmt = (
            select(UserModel.balance)
            .where(UserModel.id == user_id)
            .with_for_update()
        )
        balance = (await self._session.execute(stmt)).scalar_one_or_none()
        if balance is None:
            raise ValueError(f"User #{user_id} không tồn tại.")
        return balance

    async def update_balance(self, user_id: int, new_balance: Decimal) -> User:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(balance=new_balance)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            raise ValueError(f"User #{user_id} không tồn tại.")
        return _to_entity(m)

    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[User], int]:
        stmt = select(UserModel)
        count_stmt = select(func.count(UserModel.id))
        if search:
            pat = f"%{search}%"
            cond = or_(
                UserModel.username.ilike(pat),
                UserModel.phone.ilike(pat),
                UserModel.email.ilike(pat),
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(UserModel.id.desc()).offset((page - 1) * limit).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in rows], total

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, username: str, password_hash: str, phone: Optional[str] = None, email: Optional[str] = None) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]: ...

    @abstractmethod
    async def link_telegram(self, user_id: int, telegram_id: int, telegram_username: Optional[str]) -> User: ...

    @abstractmethod
    async def update_balance(self, user_id: int, new_balance: Decimal) -> User:
        """Gọi với SELECT FOR UPDATE từ bên ngoài transaction."""
        ...

    @abstractmethod
    async def get_balance_for_update(self, user_id: int) -> Decimal:
        """Lấy balance với SELECT FOR UPDATE (lock row)."""
        ...

    @abstractmethod
    async def list_users(self, page: int = 1, limit: int = 20, search: Optional[str] = None) -> tuple[list[User], int]: ...

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class TelegramLinkToken:
    def __init__(
        self,
        id: int,
        user_id: int,
        token: str,
        expires_at: datetime,
        used: bool,
        created_at: datetime,
    ):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.used = used
        self.created_at = created_at


class ITelegramLinkTokenRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int, token: str, expires_at: datetime) -> TelegramLinkToken: ...

    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[TelegramLinkToken]: ...

    @abstractmethod
    async def mark_used(self, token_id: int) -> None: ...

    @abstractmethod
    async def delete_expired(self) -> int: ...

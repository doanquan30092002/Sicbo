"""Use cases cho Telegram link flow: tạo token (web) và xác nhận link (bot)."""
import secrets
from datetime import datetime, timedelta, timezone

from app.domain.entities.user import User
from app.domain.repositories.telegram_link_repo import ITelegramLinkTokenRepository
from app.domain.repositories.user_repo import IUserRepository

LINK_TOKEN_TTL_MINUTES = 10


class TelegramAlreadyLinkedError(Exception):
    pass


class InvalidLinkTokenError(Exception):
    pass


class GenerateLinkToken:
    """Tạo 6-digit numeric token cho user đã login. User dùng token để /link trong bot."""

    def __init__(self, token_repo: ITelegramLinkTokenRepository):
        self._repo = token_repo

    async def execute(self, user_id: int) -> tuple[str, datetime]:
        token = "".join(secrets.choice("0123456789") for _ in range(6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=LINK_TOKEN_TTL_MINUTES)
        rec = await self._repo.create(user_id, token, expires_at)
        return rec.token, rec.expires_at


class LinkTelegram:
    """Bot gọi khi user nhập /link <token>. Liên kết telegram_id với user."""

    def __init__(
        self,
        token_repo: ITelegramLinkTokenRepository,
        user_repo: IUserRepository,
    ):
        self._token_repo = token_repo
        self._user_repo = user_repo

    async def execute(
        self,
        token: str,
        telegram_id: int,
        telegram_username: str | None = None,
    ) -> User:
        rec = await self._token_repo.get_by_token(token)
        if not rec:
            raise InvalidLinkTokenError("Mã liên kết không tồn tại.")
        if rec.used:
            raise InvalidLinkTokenError("Mã liên kết đã được sử dụng.")
        if rec.expires_at < datetime.now(timezone.utc):
            raise InvalidLinkTokenError("Mã liên kết đã hết hạn.")

        existing = await self._user_repo.get_by_telegram_id(telegram_id)
        if existing and existing.id != rec.user_id:
            raise TelegramAlreadyLinkedError(
                f"Tài khoản Telegram này đã liên kết với user khác."
            )

        user = await self._user_repo.link_telegram(
            rec.user_id, telegram_id, telegram_username
        )
        await self._token_repo.mark_used(rec.id)
        return user

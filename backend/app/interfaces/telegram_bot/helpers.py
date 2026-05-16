"""Telegram bot helpers — session, auth, format messages."""
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Awaitable, Callable, Optional

from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings
from app.domain.entities.user import User
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


@asynccontextmanager
async def db_session():
    """Async context manager: tự commit nếu không exception, rollback nếu có."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with db_session() as session:
        repo = UserRepository(session)
        return await repo.get_by_telegram_id(telegram_id)


def auth_required(handler: Callable[..., Awaitable]):
    """Decorator: chặn lệnh nếu user chưa liên kết Telegram."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        tg_user = update.effective_user
        if not tg_user:
            return
        user = await get_user_by_telegram_id(tg_user.id)
        if not user:
            await update.effective_message.reply_text(
                "⚠️ Bạn chưa liên kết tài khoản.\n"
                "1. Đăng nhập web → Tạo mã liên kết.\n"
                "2. Gõ: `/link <mã 6 số>`",
                parse_mode="Markdown",
            )
            return
        if not user.is_active:
            await update.effective_message.reply_text("🚫 Tài khoản đã bị khoá.")
            return
        context.user_data["sicbo_user_id"] = user.id
        return await handler(update, context, user, *args, **kwargs)

    return wrapper


def admin_required(handler: Callable[..., Awaitable]):
    """Decorator: chặn lệnh nếu telegram_id không trong TELEGRAM_ADMIN_IDS."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        tg_user = update.effective_user
        if not tg_user or tg_user.id not in settings.admin_telegram_ids:
            await update.effective_message.reply_text("🚫 Bạn không có quyền admin.")
            return
        return await handler(update, context, *args, **kwargs)

    return wrapper


def fmt_money(amount) -> str:
    return f"{amount:,.0f} VND"

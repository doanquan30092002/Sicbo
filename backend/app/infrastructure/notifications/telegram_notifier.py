"""Telegram notifier — gửi tin nhắn user + admin qua python-telegram-bot Application."""
import logging
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from app.application.ports.notification_port import INotificationPort
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier(INotificationPort):
    """Wrapper quanh telegram.Bot. Dùng singleton-style bot instance để tránh tạo session mỗi lần."""

    def __init__(self, bot: Optional[Bot] = None, admin_chat_id: Optional[str] = None):
        token = settings.telegram_bot_token
        if bot is None and not token:
            logger.warning("TELEGRAM_BOT_TOKEN chưa được cấu hình — notifier sẽ no-op.")
            self._bot = None
        else:
            self._bot = bot or Bot(token=token)
        self._admin_chat_id = admin_chat_id or settings.telegram_admin_chat_id

    async def send_user_message(self, telegram_id: int, text: str) -> bool:
        if self._bot is None:
            return False
        if not telegram_id:
            return False
        try:
            await self._bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
            return True
        except TelegramError as e:
            logger.warning(f"Không gửi được tin cho user telegram_id={telegram_id}: {e}")
            return False

    async def send_admin_message(self, text: str) -> None:
        if self._bot is None or not self._admin_chat_id:
            logger.warning("Admin chat chưa cấu hình — bỏ qua admin notification.")
            return
        try:
            await self._bot.send_message(
                chat_id=self._admin_chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except TelegramError as e:
            logger.error(f"Không gửi được tin admin: {e}")

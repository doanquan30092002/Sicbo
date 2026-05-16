"""Telegram bot Application — setup + register handlers + start/stop hooks."""
import logging
from typing import Optional

from telegram.ext import Application, CommandHandler

from app.config import settings
from app.interfaces.telegram_bot.handlers.admin import register_admin_handlers
from app.interfaces.telegram_bot.handlers.betting import build_bet_conversation
from app.interfaces.telegram_bot.handlers.common import (
    balance_cmd,
    cancel_cmd,
    help_cmd,
    link_cmd,
    me_cmd,
    start_cmd,
)
from app.interfaces.telegram_bot.handlers.lottery import mybets_cmd, result_cmd
from app.interfaces.telegram_bot.handlers.wallet import (
    build_withdraw_conversation,
    deposit_cmd,
    history_cmd,
)

logger = logging.getLogger(__name__)


def build_application() -> Optional[Application]:
    """Tạo Telegram Application. Trả None nếu chưa cấu hình TELEGRAM_BOT_TOKEN."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN chưa cấu hình — bot sẽ KHÔNG khởi động.")
        return None

    application = Application.builder().token(settings.telegram_bot_token).build()

    # Common
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("link", link_cmd))
    application.add_handler(CommandHandler("me", me_cmd))
    application.add_handler(CommandHandler("balance", balance_cmd))
    application.add_handler(CommandHandler("cancel", cancel_cmd))

    # Lottery
    application.add_handler(CommandHandler("result", result_cmd))
    application.add_handler(CommandHandler("mybets", mybets_cmd))

    # Wallet
    application.add_handler(CommandHandler("deposit", deposit_cmd))
    application.add_handler(CommandHandler("history", history_cmd))
    application.add_handler(build_withdraw_conversation())

    # Betting
    application.add_handler(build_bet_conversation())

    # Admin
    register_admin_handlers(application)

    logger.info("Telegram bot Application đã build xong.")
    return application


async def start_bot(application: Application) -> None:
    """Khởi động bot dưới dạng polling task. Gọi trong FastAPI lifespan."""
    await application.initialize()
    await application.start()
    if application.updater:
        await application.updater.start_polling(drop_pending_updates=True)
    logger.info("✅ Telegram bot đang chạy (polling).")


async def stop_bot(application: Application) -> None:
    """Dừng bot gracefully."""
    if application.updater and application.updater.running:
        await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logger.info("🛑 Telegram bot đã dừng.")

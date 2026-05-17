"""Telegram webhook endpoint — nhận update từ Telegram thay vì long polling.

Telegram sẽ POST tới URL này khi user gửi message. Thêm vào update_queue của
PTB Application để các handler xử lý như khi polling.
"""
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status
from telegram import Update

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    expected = settings.telegram_webhook_secret
    if expected and x_telegram_bot_api_secret_token != expected:
        logger.warning("Telegram webhook: secret token không hợp lệ.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret")

    bot_app = getattr(request.app.state, "bot", None)
    if bot_app is None:
        logger.error("Telegram webhook: bot chưa khởi tạo trong app.state.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bot not running")

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Telegram webhook: body không phải JSON: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    update = Update.de_json(data, bot_app.bot)
    await bot_app.update_queue.put(update)
    return {"ok": True}

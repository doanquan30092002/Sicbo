"""FastAPI app entry — CORS, lifespan, routers."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import games để register vào GameRegistry
import app.domain.games  # noqa: F401
from app.config import settings
from app.interfaces.api.routers import admin, auth, bets, games, lottery, wallet, webhooks
from app.interfaces.scheduler.jobs import build_scheduler
from app.interfaces.telegram_bot.bot import build_application, start_bot, stop_bot

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Khởi động Sicbo API — env={settings.environment}")

    # APScheduler — fetch result + settle bets cho mọi active game
    scheduler = build_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("✅ APScheduler đã chạy.")

    # Telegram bot — chạy cùng process qua python-telegram-bot Application
    bot_app = build_application()
    if bot_app is not None:
        await start_bot(bot_app)
        app.state.bot = bot_app
    else:
        app.state.bot = None

    try:
        yield
    finally:
        logger.info("Tắt Sicbo API…")
        if app.state.bot is not None:
            try:
                await stop_bot(app.state.bot)
            except Exception as e:
                logger.exception(f"Lỗi khi tắt bot: {e}")
        try:
            scheduler.shutdown(wait=False)
        except Exception as e:
            logger.exception(f"Lỗi khi tắt scheduler: {e}")


app = FastAPI(
    title="Sicbo API",
    description="API cho hệ thống cờ bạc số đề Sicbo dựa trên XSMB.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "env": settings.environment}


app.include_router(auth.router)
app.include_router(games.router)
app.include_router(bets.router)
app.include_router(lottery.router)
app.include_router(wallet.router)
app.include_router(webhooks.router)
app.include_router(admin.router)

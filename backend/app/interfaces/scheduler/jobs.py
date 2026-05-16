"""APScheduler jobs — tự động fetch result + settle bets cho mỗi active game.

Lịch chạy (timezone Asia/Ho_Chi_Minh):
- {result_time}        → fetch_result_job (vd XSMB: 18:30)
- {result_time + 5m}   → settle_bets_job  (vd XSMB: 18:35)
- {result_time + 15m}  → retry_fetch_job  (nếu chưa có kết quả)
"""
import logging
from datetime import date, datetime, time, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.use_cases.betting.settle_bets import SettleBets
from app.application.use_cases.lottery.fetch_and_store_result import FetchAndStoreResult
from app.domain.games.registry import GameRegistry
from app.infrastructure.database.repositories.bet_repository import BetRepository
from app.infrastructure.database.repositories.game_result_repository import (
    GameResultRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.external.xsmb_fetcher import XSMBFetcher
from app.infrastructure.notifications.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def _add_minutes(t: time, minutes: int) -> time:
    """Cộng phút vào datetime.time (clamp trong cùng ngày)."""
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


async def fetch_result_job(game_id: str) -> None:
    """Fetch kết quả XSMB hôm nay và lưu vào DB."""
    today = datetime.now(VN_TZ).date()
    logger.info(f"[scheduler] fetch_result_job game={game_id} date={today}")

    async with AsyncSessionLocal() as session:
        try:
            repo = GameResultRepository(session)
            fetcher = XSMBFetcher() if game_id == "xsmb" else None
            if fetcher is None:
                logger.error(f"[scheduler] Không có fetcher cho game '{game_id}'.")
                return

            uc = FetchAndStoreResult(repo, fetcher)
            await uc.execute(game_id, today)
            await session.commit()
            logger.info(f"[scheduler] ✅ fetch_result_job xong: {game_id}/{today}")
        except Exception as e:
            await session.rollback()
            logger.exception(f"[scheduler] ❌ fetch_result_job fail: {e}")


async def settle_bets_job(game_id: str) -> None:
    """Tính thắng/thua + payout cho toàn bộ bets hôm nay của game_id."""
    today = datetime.now(VN_TZ).date()
    logger.info(f"[scheduler] settle_bets_job game={game_id} date={today}")

    async with AsyncSessionLocal() as session:
        try:
            bet_repo = BetRepository(session)
            user_repo = UserRepository(session)
            wallet_repo = WalletRepository(session)
            result_repo = GameResultRepository(session)
            notifier = TelegramNotifier()

            uc = SettleBets(bet_repo, result_repo, user_repo, wallet_repo, notifier)
            stats = await uc.execute(game_id, today)
            await session.commit()
            logger.info(f"[scheduler] ✅ settle_bets_job xong: {stats}")
        except Exception as e:
            await session.rollback()
            logger.exception(f"[scheduler] ❌ settle_bets_job fail: {e}")


async def retry_fetch_job(game_id: str) -> None:
    """Retry fetch sau 15 phút nếu chưa có kết quả."""
    today = datetime.now(VN_TZ).date()
    async with AsyncSessionLocal() as session:
        repo = GameResultRepository(session)
        existing = await repo.get_by_game_and_date(game_id, today)
        if existing:
            logger.info(f"[scheduler] retry_fetch_job skip — đã có kết quả {game_id}/{today}")
            return
    logger.warning(f"[scheduler] Retry fetch cho {game_id}/{today}")
    await fetch_result_job(game_id)


def register_game_jobs(scheduler: AsyncIOScheduler) -> None:
    """Đăng ký jobs cho TẤT CẢ active games trong GameRegistry.

    Mỗi game đóng góp 3 jobs: fetch (result_time), settle (+5m), retry (+15m).
    """
    for game in GameRegistry.all_active():
        rt = game.result_time
        rt_plus5 = _add_minutes(rt, 5)
        rt_plus15 = _add_minutes(rt, 15)

        scheduler.add_job(
            fetch_result_job,
            CronTrigger(hour=rt.hour, minute=rt.minute, timezone=VN_TZ),
            args=[game.game_id],
            id=f"fetch_{game.game_id}",
            replace_existing=True,
        )
        scheduler.add_job(
            settle_bets_job,
            CronTrigger(hour=rt_plus5.hour, minute=rt_plus5.minute, timezone=VN_TZ),
            args=[game.game_id],
            id=f"settle_{game.game_id}",
            replace_existing=True,
        )
        scheduler.add_job(
            retry_fetch_job,
            CronTrigger(hour=rt_plus15.hour, minute=rt_plus15.minute, timezone=VN_TZ),
            args=[game.game_id],
            id=f"retry_{game.game_id}",
            replace_existing=True,
        )
        logger.info(
            f"[scheduler] Đăng ký jobs cho '{game.game_id}': "
            f"fetch={rt.strftime('%H:%M')}, settle={rt_plus5.strftime('%H:%M')}, retry={rt_plus15.strftime('%H:%M')}"
        )


def build_scheduler() -> AsyncIOScheduler:
    """Tạo scheduler + đăng ký tất cả jobs. Caller phải gọi .start() / .shutdown()."""
    scheduler = AsyncIOScheduler(timezone=VN_TZ)
    register_game_jobs(scheduler)
    return scheduler

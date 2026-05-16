"""Lottery bot handlers: /result, /mybets."""
import logging
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from app.infrastructure.database.repositories.bet_repository import BetRepository
from app.infrastructure.database.repositories.game_result_repository import (
    GameResultRepository,
)
from app.interfaces.telegram_bot.helpers import auth_required, db_session, fmt_money

logger = logging.getLogger(__name__)

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """`/result` — hiển thị 2 số cuối Đặc Biệt + đầu lô của XSMB hôm nay."""
    today = datetime.now(VN_TZ).date()
    async with db_session() as session:
        repo = GameResultRepository(session)
        result = await repo.get_by_game_and_date("xsmb", today)

    if not result:
        await update.message.reply_text(
            f"⏳ Chưa có kết quả XSMB ngày {today.strftime('%d/%m/%Y')}.\n"
            f"Kết quả thường có lúc 18:30.",
        )
        return

    data = result.parsed_data or {}
    special = data.get("special", "—")
    de = data.get("de_number", special[-2:] if special and len(special) >= 2 else "—")
    all_last2 = data.get("all_last2", [])

    # Group last2 by first digit (đầu lô)
    dau_lo: dict[str, list[str]] = {str(i): [] for i in range(10)}
    for n in all_last2:
        if isinstance(n, str) and len(n) == 2 and n[0].isdigit():
            dau_lo[n[0]].append(n[1])

    lines = [
        f"🎯 *KẾT QUẢ XSMB {today.strftime('%d/%m/%Y')}*",
        "━━━━━━━━━━━━━━━━",
        f"🏆 Đặc Biệt: *{special}*",
        f"🎯 Đề (2 số cuối): *{de}*",
        "",
        "📊 *Đầu lô:*",
    ]
    for d, nums in dau_lo.items():
        if nums:
            lines.append(f"  {d}: {', '.join(nums)}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth_required
async def mybets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """`/mybets` — liệt kê cược hôm nay của user."""
    today = datetime.now(VN_TZ).date()
    async with db_session() as session:
        bet_repo = BetRepository(session)
        bets, total = await bet_repo.get_user_bets(
            user_id=user.id,
            draw_date=today,
            page=1,
            limit=20,
        )

    if not bets:
        await update.message.reply_text(f"📭 Bạn chưa cược nào hôm nay.")
        return

    status_icons = {
        "pending": "⏳",
        "won": "🎉",
        "lost": "❌",
        "cancelled": "🚫",
    }
    lines = [
        f"🎲 *CƯỢC HÔM NAY ({total})*",
        f"━━━━━━━━━━━━━━━━",
    ]
    for b in bets:
        icon = status_icons.get(b.status, "•")
        nums = ",".join(b.numbers[:5]) + ("…" if len(b.numbers) > 5 else "")
        lines.append(
            f"{icon} #{b.id} {b.bet_type_id} [{nums}] "
            f"× {fmt_money(b.total_stake)} → {fmt_money(b.win_amount or 0)}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

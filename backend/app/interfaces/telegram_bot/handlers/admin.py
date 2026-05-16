"""Admin bot handlers: /admin_stats, /pending_withdrawals, approve/reject."""
import logging
from datetime import datetime

import pytz
from sqlalchemy import func, select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app.application.use_cases.admin.process_withdrawal import ProcessWithdrawal
from app.domain.value_objects.bet_type import WithdrawalStatus
from app.infrastructure.database.models.bet_model import BetModel
from app.infrastructure.database.models.transaction_model import WithdrawalModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.infrastructure.notifications.telegram_notifier import TelegramNotifier
from app.interfaces.telegram_bot.helpers import admin_required, db_session, fmt_money

logger = logging.getLogger(__name__)

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


@admin_required
async def admin_stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(VN_TZ).date()
    async with db_session() as session:
        total_users = (await session.execute(select(func.count(UserModel.id)))).scalar_one()
        pending_w = (
            await session.execute(
                select(func.count(WithdrawalModel.id)).where(
                    WithdrawalModel.status == WithdrawalStatus.PENDING.value
                )
            )
        ).scalar_one()
        today_bets = (
            await session.execute(
                select(func.count(BetModel.id)).where(BetModel.draw_date == today)
            )
        ).scalar_one()
        today_stake = (
            await session.execute(
                select(func.coalesce(func.sum(BetModel.total_stake), 0)).where(
                    BetModel.draw_date == today
                )
            )
        ).scalar_one()
        today_payout = (
            await session.execute(
                select(func.coalesce(func.sum(BetModel.win_amount), 0)).where(
                    BetModel.draw_date == today
                )
            )
        ).scalar_one()

    text = (
        f"📊 *ADMIN STATS — {today.strftime('%d/%m/%Y')}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👥 Users: {total_users}\n"
        f"💸 Pending withdrawals: {pending_w}\n"
        f"🎲 Bets hôm nay: {today_bets}\n"
        f"💰 Tổng cược: {fmt_money(today_stake)}\n"
        f"🎉 Tổng trả thưởng: {fmt_money(today_payout)}\n"
        f"📈 Net: {fmt_money(today_stake - today_payout)}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@admin_required
async def pending_withdrawals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with db_session() as session:
        wallet_repo = WalletRepository(session)
        items, total = await wallet_repo.get_pending_withdrawals(page=1, limit=10)

    if not items:
        await update.message.reply_text("✅ Không có yêu cầu rút nào đang chờ duyệt.")
        return

    await update.message.reply_text(f"💸 *{total} yêu cầu chờ duyệt:*", parse_mode="Markdown")
    for w in items:
        text = (
            f"📋 #{w.id} — *{fmt_money(w.amount)}*\n"
            f"👤 User: {w.user_id}\n"
            f"🏦 {w.bank_name or w.payment_method}: `{w.account_number}`\n"
            f"👤 {w.account_name}\n"
            f"🗓 {w.requested_at.strftime('%d/%m %H:%M')}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Duyệt", callback_data=f"adm:approve:{w.id}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"adm:reject:{w.id}"),
        ]])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


@admin_required
async def admin_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3:
        return
    _, action, wid_str = parts
    try:
        wid = int(wid_str)
    except ValueError:
        return

    admin_tg_id = query.from_user.id
    try:
        async with db_session() as session:
            user_repo = UserRepository(session)
            admin_user = await user_repo.get_by_telegram_id(admin_tg_id)
            if not admin_user or not admin_user.is_admin:
                # Fallback: cho phép admin theo TELEGRAM_ADMIN_IDS dùng admin_id = 0
                admin_db_id = 0
            else:
                admin_db_id = admin_user.id

            wallet_repo = WalletRepository(session)
            notifier = TelegramNotifier()
            uc = ProcessWithdrawal(wallet_repo, user_repo, notifier)

            if action == "approve":
                w = await uc.approve(wid, admin_db_id)
                await query.edit_message_text(
                    query.message.text + f"\n\n✅ *Đã duyệt* bởi @{query.from_user.username or admin_tg_id}",
                    parse_mode="Markdown",
                )
            elif action == "reject":
                w = await uc.reject(wid, admin_db_id, reason="Admin từ chối qua bot")
                await query.edit_message_text(
                    query.message.text + f"\n\n❌ *Đã từ chối* bởi @{query.from_user.username or admin_tg_id}",
                    parse_mode="Markdown",
                )
            else:
                return
    except Exception as e:
        logger.exception(f"Admin action failed: {e}")
        await query.edit_message_text(query.message.text + f"\n\n⚠️ Lỗi: {e}")
        return

    logger.info(f"Admin {admin_tg_id} {action} withdrawal #{wid}")


def register_admin_handlers(application) -> None:
    application.add_handler(CommandHandler("admin_stats", admin_stats_cmd))
    application.add_handler(CommandHandler("pending_withdrawals", pending_withdrawals_cmd))
    application.add_handler(CallbackQueryHandler(admin_action_callback, pattern=r"^adm:"))

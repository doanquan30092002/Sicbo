"""Wallet bot handlers: /deposit, /withdraw, /history."""
import logging
import re
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.application.use_cases.wallet.request_deposit import RequestDeposit
from app.application.use_cases.wallet.request_withdrawal import (
    InsufficientBalanceError,
    RequestWithdrawal,
)
from app.config import settings
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.infrastructure.notifications.telegram_notifier import TelegramNotifier
from app.interfaces.telegram_bot.helpers import auth_required, db_session, fmt_money

logger = logging.getLogger(__name__)


# ---------- /deposit (single command, returns instructions) ----------

@auth_required
async def deposit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    """`/deposit <amount>` — tạo lệnh nạp + hướng dẫn chuyển khoản."""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Cú pháp: `/deposit <số tiền>`\n"
            "Ví dụ: `/deposit 100000` — nạp 100,000 VND",
            parse_mode="Markdown",
        )
        return

    try:
        amount = Decimal(args[0].replace(",", "").replace(".", ""))
    except Exception:
        await update.message.reply_text("❌ Số tiền không hợp lệ.")
        return

    try:
        async with db_session() as session:
            wallet_repo = WalletRepository(session)
            uc = RequestDeposit(wallet_repo, settings.bank_account_no, settings.momo_phone)
            deposit = await uc.execute(user.id, amount, "bank_transfer")
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    text = (
        f"💵 *HƯỚNG DẪN NẠP TIỀN*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🏦 Ngân hàng: *{settings.bank_name}*\n"
        f"💳 STK: `{settings.bank_account_no}`\n"
        f"👤 Tên: *{settings.bank_account_name}*\n"
        f"💰 Số tiền: *{fmt_money(deposit.amount)}*\n"
        f"📝 Nội dung CK: `{deposit.transfer_content}`\n\n"
        f"⚠️ *Phải đúng nội dung* để hệ thống tự cộng tiền.\n"
        f"⏱ Tiền sẽ tự về sau 1-2 phút."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ---------- /withdraw conversation ----------

WD_AMOUNT, WD_BANK_NAME, WD_ACCOUNT_NO, WD_ACCOUNT_NAME, WD_CONFIRM = range(5)


@auth_required
async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    context.user_data["wd"] = {}
    await update.message.reply_text(
        f"💸 *RÚT TIỀN*\n"
        f"Số dư: *{fmt_money(user.balance)}*\n"
        f"Tối thiểu: 50,000 VND.\n\n"
        f"Gửi số tiền muốn rút (VD: 100000):",
        parse_mode="Markdown",
    )
    return WD_AMOUNT


async def wd_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = Decimal(update.message.text.strip().replace(",", "").replace(".", ""))
    except Exception:
        await update.message.reply_text("❌ Số tiền không hợp lệ. Gõ lại hoặc /cancel.")
        return WD_AMOUNT

    if amount < Decimal(50000):
        await update.message.reply_text("❌ Tối thiểu 50,000 VND. Gõ lại hoặc /cancel.")
        return WD_AMOUNT

    context.user_data["wd"]["amount"] = amount
    await update.message.reply_text("Tên ngân hàng (VD: Vietcombank):")
    return WD_BANK_NAME


async def wd_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["wd"]["bank_name"] = update.message.text.strip()
    await update.message.reply_text("Số tài khoản:")
    return WD_ACCOUNT_NO


async def wd_account_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc = update.message.text.strip()
    if not re.match(r"^\d{6,30}$", acc):
        await update.message.reply_text("❌ Số tài khoản không hợp lệ. Gõ lại hoặc /cancel.")
        return WD_ACCOUNT_NO
    context.user_data["wd"]["account_number"] = acc
    await update.message.reply_text("Tên chủ tài khoản (in hoa, không dấu):")
    return WD_ACCOUNT_NAME


async def wd_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip().upper()
    context.user_data["wd"]["account_name"] = name
    wd = context.user_data["wd"]
    text = (
        f"📋 *Xác nhận yêu cầu rút*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💵 Số tiền: *{fmt_money(wd['amount'])}*\n"
        f"🏦 Bank: *{wd['bank_name']}*\n"
        f"💳 STK: `{wd['account_number']}`\n"
        f"👤 Tên: *{wd['account_name']}*\n\n"
        f"Bấm nút để xác nhận:"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Xác nhận", callback_data="wd:confirm"),
            InlineKeyboardButton("❌ Huỷ", callback_data="wd:cancel"),
        ]
    ])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    return WD_CONFIRM


async def wd_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "wd:cancel":
        context.user_data.pop("wd", None)
        await query.edit_message_text("❌ Đã huỷ yêu cầu rút.")
        return ConversationHandler.END

    wd = context.user_data.get("wd")
    if not wd:
        await query.edit_message_text("⚠️ Phiên đã hết. Gõ /withdraw để bắt đầu lại.")
        return ConversationHandler.END

    user_id = context.user_data.get("sicbo_user_id")
    if not user_id:
        await query.edit_message_text("⚠️ Lỗi phiên. Vui lòng /withdraw lại.")
        return ConversationHandler.END

    try:
        async with db_session() as session:
            wallet_repo = WalletRepository(session)
            user_repo = UserRepository(session)
            notifier = TelegramNotifier()
            uc = RequestWithdrawal(wallet_repo, user_repo, notifier)
            withdrawal = await uc.execute(
                user_id=user_id,
                amount=wd["amount"],
                payment_method="bank_transfer",
                account_number=wd["account_number"],
                account_name=wd["account_name"],
                bank_name=wd["bank_name"],
            )
    except InsufficientBalanceError as e:
        await query.edit_message_text(f"❌ {e}")
        return ConversationHandler.END
    except ValueError as e:
        await query.edit_message_text(f"❌ {e}")
        return ConversationHandler.END

    context.user_data.pop("wd", None)
    await query.edit_message_text(
        f"✅ Đã gửi yêu cầu rút *{fmt_money(withdrawal.amount)}*.\n"
        f"📋 Mã: #{withdrawal.id}\n"
        f"⏱ Admin sẽ duyệt trong thời gian sớm nhất.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


def build_withdraw_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("withdraw", withdraw_start)],
        states={
            WD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, wd_amount)],
            WD_BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, wd_bank_name)],
            WD_ACCOUNT_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, wd_account_no)],
            WD_ACCOUNT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, wd_account_name)],
            WD_CONFIRM: [CallbackQueryHandler(wd_confirm_callback, pattern=r"^wd:")],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
        name="withdraw_conv",
    )


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("wd", None)
    await update.message.reply_text("❌ Đã huỷ.")
    return ConversationHandler.END


# ---------- /history ----------

@auth_required
async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    async with db_session() as session:
        wallet_repo = WalletRepository(session)
        txs, _ = await wallet_repo.get_transactions(user.id, page=1, limit=10)

    if not txs:
        await update.message.reply_text("📜 Chưa có giao dịch nào.")
        return

    lines = ["📜 *10 GIAO DỊCH GẦN NHẤT*", "━━━━━━━━━━━━━━━━"]
    icons = {
        "deposit": "💵",
        "withdraw": "💸",
        "bet_debit": "🎲",
        "win_credit": "🎉",
        "refund": "↩️",
    }
    for t in txs:
        icon = icons.get(t.type, "•")
        sign = "+" if t.type in ("deposit", "win_credit", "refund") else "-"
        lines.append(
            f"{icon} {sign}{fmt_money(t.amount)} — {t.type} ({t.created_at.strftime('%d/%m %H:%M')})"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

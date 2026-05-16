"""Common bot handlers: /start, /help, /link, /unlink."""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.application.use_cases.auth.telegram_link import (
    InvalidLinkTokenError,
    LinkTelegram,
    TelegramAlreadyLinkedError,
)
from app.infrastructure.database.repositories.telegram_link_repository import (
    TelegramLinkTokenRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.interfaces.telegram_bot.helpers import (
    auth_required,
    db_session,
    fmt_money,
    get_user_by_telegram_id,
)

logger = logging.getLogger(__name__)


WELCOME = (
    "🎰 *Chào mừng đến Sicbo!*\n"
    "Nạp 1 phút — rút 1 giây.\n\n"
    "Để bắt đầu:\n"
    "1️⃣ Đăng ký tài khoản trên web\n"
    "2️⃣ Tạo mã liên kết Telegram\n"
    "3️⃣ Gõ: `/link <mã 6 số>`\n\n"
    "Gõ /help để xem danh sách lệnh."
)

HELP = (
    "📖 *DANH SÁCH LỆNH*\n\n"
    "🔑 *Tài khoản*\n"
    "/link <code> — Liên kết tài khoản\n"
    "/me — Xem thông tin\n"
    "/balance — Xem số dư\n\n"
    "🎲 *Cá cược*\n"
    "/bet — Đặt cược (interactive)\n"
    "/mybets — Cược hôm nay\n"
    "/history — Lịch sử cược\n\n"
    "💰 *Ví*\n"
    "/deposit — Hướng dẫn nạp tiền\n"
    "/withdraw — Rút tiền\n\n"
    "🎯 *Kết quả*\n"
    "/result — Kết quả XSMB hôm nay\n\n"
    "⚙️ *Khác*\n"
    "/cancel — Huỷ thao tác hiện tại\n"
    "/help — Hiện trợ giúp này"
)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_telegram_id(update.effective_user.id)
    if user:
        await update.message.reply_text(
            f"👋 Chào *{user.username}*!\n"
            f"💰 Số dư: *{fmt_money(user.balance)}*\n\n"
            f"Gõ /help để xem danh sách lệnh.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(WELCOME, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP, parse_mode="Markdown")


async def link_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """`/link <token>` — liên kết Telegram với tài khoản."""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Cú pháp: `/link <mã 6 số>`\n"
            "Vào web → Cài đặt → Liên kết Telegram để lấy mã.",
            parse_mode="Markdown",
        )
        return

    token = args[0].strip()
    tg_user = update.effective_user

    try:
        async with db_session() as session:
            token_repo = TelegramLinkTokenRepository(session)
            user_repo = UserRepository(session)
            uc = LinkTelegram(token_repo, user_repo)
            user = await uc.execute(
                token=token,
                telegram_id=tg_user.id,
                telegram_username=tg_user.username,
            )
    except InvalidLinkTokenError as e:
        await update.message.reply_text(f"❌ {e}")
        return
    except TelegramAlreadyLinkedError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    await update.message.reply_text(
        f"✅ Liên kết thành công!\n"
        f"👤 Tài khoản: *{user.username}*\n"
        f"💰 Số dư: *{fmt_money(user.balance)}*\n\n"
        f"Gõ /help để xem danh sách lệnh.",
        parse_mode="Markdown",
    )


@auth_required
async def me_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    text = (
        f"👤 *Tài khoản*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Username: `{user.username}`\n"
        f"💰 Số dư: *{fmt_money(user.balance)}*\n"
        f"📱 Telegram: @{user.telegram_username or '—'}\n"
        f"🗓 Đăng ký: {user.created_at.strftime('%Y-%m-%d')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@auth_required
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    await update.message.reply_text(
        f"💰 Số dư của bạn: *{fmt_money(user.balance)}*",
        parse_mode="Markdown",
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Đã huỷ thao tác hiện tại.")

"""Betting bot handler: /bet ConversationHandler."""
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

from app.application.use_cases.betting.place_bet import (
    CutoffPassedError,
    InsufficientBalanceError,
    PlaceBet,
)
from app.domain.games.registry import GameRegistry
from app.infrastructure.database.repositories.bet_repository import BetRepository
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.interfaces.telegram_bot.helpers import auth_required, db_session, fmt_money

logger = logging.getLogger(__name__)


# Conversation states
B_GAME, B_BET_TYPE, B_NUMBERS, B_STAKE, B_CONFIRM = range(5)


@auth_required
async def bet_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    games = list(GameRegistry.all_active())
    if not games:
        await update.message.reply_text("⚠️ Hiện không có game nào đang mở.")
        return ConversationHandler.END

    context.user_data["bet"] = {}
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(g.game_name, callback_data=f"bet:game:{g.game_id}")] for g in games]
        + [[InlineKeyboardButton("❌ Huỷ", callback_data="bet:cancel")]]
    )
    await update.message.reply_text(
        f"🎲 *ĐẶT CƯỢC*\n💰 Số dư: *{fmt_money(user.balance)}*\n\nChọn trò chơi:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    return B_GAME


async def bet_pick_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bet:cancel":
        return await _cancel(update, context)

    game_id = query.data.split(":")[2]
    try:
        game = GameRegistry.get(game_id)
    except ValueError:
        await query.edit_message_text("❌ Game không tồn tại.")
        return ConversationHandler.END

    context.user_data["bet"]["game_id"] = game_id
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                f"{bt.display_name} (1:{bt.odds:g})",
                callback_data=f"bet:type:{bt.type_id}",
            )]
            for bt in game.get_bet_types()
        ]
        + [[InlineKeyboardButton("❌ Huỷ", callback_data="bet:cancel")]]
    )
    await query.edit_message_text(
        f"🎲 *{game.game_name}*\nChọn loại cược:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
    return B_BET_TYPE


async def bet_pick_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bet:cancel":
        return await _cancel(update, context)

    bet_type_id = query.data.split(":")[2]
    bet = context.user_data["bet"]
    bet["bet_type_id"] = bet_type_id

    game = GameRegistry.get(bet["game_id"])
    bt = game.get_bet_type(bet_type_id)
    await query.edit_message_text(
        f"🎲 {game.game_name} — *{bt.display_name}* (1:{bt.odds:g})\n"
        f"{bt.description}\n\n"
        f"Nhập các số (cách nhau bởi dấu phẩy, VD: `23,47,89`).\n"
        f"Tối thiểu {bt.min_numbers}, tối đa {bt.max_numbers} số.\n"
        f"Gõ /cancel để huỷ.",
        parse_mode="Markdown",
    )
    return B_NUMBERS


async def bet_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip()
    parts = [p.strip().zfill(2) for p in re.split(r"[,\s]+", raw) if p.strip()]
    invalid = [p for p in parts if not re.match(r"^\d{2}$", p)]
    if invalid or not parts:
        await update.message.reply_text(
            "❌ Số không hợp lệ. Nhập 00-99, cách nhau bằng dấu phẩy. /cancel để huỷ."
        )
        return B_NUMBERS

    bet = context.user_data["bet"]
    game = GameRegistry.get(bet["game_id"])
    bt = game.get_bet_type(bet["bet_type_id"])
    if len(parts) < bt.min_numbers or len(parts) > bt.max_numbers:
        await update.message.reply_text(
            f"❌ Phải có từ {bt.min_numbers} đến {bt.max_numbers} số."
        )
        return B_NUMBERS

    bet["numbers"] = parts
    await update.message.reply_text(
        f"✅ Đã chọn: `{', '.join(parts)}`\n\n"
        f"Nhập số điểm × tiền/điểm (VD: `5x10000` hoặc chỉ tiền/điểm `10000`):",
        parse_mode="Markdown",
    )
    return B_STAKE


async def bet_stake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip().lower().replace(" ", "")
    m = re.match(r"^(?:(\d+)x)?(\d+)$", raw)
    if not m:
        await update.message.reply_text(
            "❌ Định dạng sai. VD: `5x10000` (5 điểm × 10k) hoặc `10000`. /cancel để huỷ."
        )
        return B_STAKE

    points = int(m.group(1)) if m.group(1) else 1
    stake = Decimal(m.group(2))
    if points < 1 or points > 100:
        await update.message.reply_text("❌ Số điểm phải từ 1 đến 100.")
        return B_STAKE
    if stake <= 0:
        await update.message.reply_text("❌ Tiền/điểm phải > 0.")
        return B_STAKE

    bet = context.user_data["bet"]
    bet["stake_per_point"] = stake
    bet["points"] = points

    game = GameRegistry.get(bet["game_id"])
    bt = game.get_bet_type(bet["bet_type_id"])
    total_stake = stake * points * len(bet["numbers"])  # đối với Lô — mỗi con là 1 đơn vị
    # Tổng cược thực tế tính trong PlaceBet theo công thức stake * points
    # Hiển thị ước lượng đơn giản:
    estimated_potential = stake * bt.odds * points

    text = (
        f"📋 *XÁC NHẬN CƯỢC*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎲 {game.game_name} — *{bt.display_name}*\n"
        f"🔢 Số: `{', '.join(bet['numbers'])}`\n"
        f"💵 {fmt_money(stake)} × {points} điểm\n"
        f"💰 Tổng cược: *{fmt_money(stake * points)}*\n"
        f"🎯 Có thể trúng: *{fmt_money(estimated_potential)}/con*\n"
        f"━━━━━━━━━━━━━━━━"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Đặt cược", callback_data="bet:confirm"),
        InlineKeyboardButton("❌ Huỷ", callback_data="bet:cancel"),
    ]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    # Note: total_stake variable used to show full info; not part of final placement
    _ = total_stake
    return B_CONFIRM


async def bet_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "bet:cancel":
        return await _cancel(update, context)

    bet = context.user_data.get("bet")
    user_id = context.user_data.get("sicbo_user_id")
    if not bet or not user_id:
        await query.edit_message_text("⚠️ Phiên đã hết. /bet để bắt đầu lại.")
        return ConversationHandler.END

    try:
        async with db_session() as session:
            bet_repo = BetRepository(session)
            user_repo = UserRepository(session)
            wallet_repo = WalletRepository(session)
            uc = PlaceBet(bet_repo, user_repo, wallet_repo)
            placed = await uc.execute(
                user_id=user_id,
                game_id=bet["game_id"],
                bet_type_id=bet["bet_type_id"],
                numbers=bet["numbers"],
                stake_per_point=bet["stake_per_point"],
                points=bet["points"],
                source="telegram",
            )
    except CutoffPassedError as e:
        await query.edit_message_text(f"⏰ {e}")
        return ConversationHandler.END
    except InsufficientBalanceError as e:
        await query.edit_message_text(f"💸 {e}")
        return ConversationHandler.END
    except ValueError as e:
        await query.edit_message_text(f"❌ {e}")
        return ConversationHandler.END

    context.user_data.pop("bet", None)
    await query.edit_message_text(
        f"✅ *Đặt cược thành công!*\n"
        f"📋 Mã: #{placed.id}\n"
        f"💰 Tổng cược: {fmt_money(placed.total_stake)}\n"
        f"🎯 Có thể trúng: {fmt_money(placed.potential_win)}\n\n"
        f"Kết quả sẽ thông báo lúc 18:35.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("bet", None)
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ Đã huỷ đặt cược.")
    else:
        await update.message.reply_text("❌ Đã huỷ đặt cược.")
    return ConversationHandler.END


def build_bet_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("bet", bet_start)],
        states={
            B_GAME: [CallbackQueryHandler(bet_pick_game, pattern=r"^bet:(game|cancel)")],
            B_BET_TYPE: [CallbackQueryHandler(bet_pick_type, pattern=r"^bet:(type|cancel)")],
            B_NUMBERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bet_numbers)],
            B_STAKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bet_stake)],
            B_CONFIRM: [CallbackQueryHandler(bet_confirm, pattern=r"^bet:(confirm|cancel)")],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
        per_user=True,
        per_chat=True,
        per_message=False,
        name="bet_conv",
    )

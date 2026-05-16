---
name: telegram-bot-dev
description: Agent chuyên phát triển Telegram Bot cho Sicbo. Dùng khi cần thêm commands, ConversationHandler, hoặc admin features trong bot.
---

# Telegram Bot Developer Agent

## Context
Bot dùng `python-telegram-bot 20.x` (async). Chạy cùng process với FastAPI qua `asyncio.create_task`.

## Cấu trúc Bot

```
interfaces/telegram_bot/
├── bot.py                    # Application builder, register handlers
└── handlers/
    ├── start.py              # /start, /help
    ├── betting.py            # /bet - ConversationHandler
    ├── wallet.py             # /balance, /deposit, /withdraw
    ├── results.py            # /ketqua, /lichsu
    └── admin.py              # /pending_withdrawals (admin only)
```

## Pattern ConversationHandler (Đặt Cược)

```python
CHOOSE_GAME, CHOOSE_TYPE, ENTER_NUMBERS, ENTER_POINTS, CONFIRM = range(5)

bet_handler = ConversationHandler(
    entry_points=[CommandHandler("bet", start_bet)],
    states={
        CHOOSE_GAME: [CallbackQueryHandler(choose_game)],
        CHOOSE_TYPE: [CallbackQueryHandler(choose_bet_type)],
        ENTER_NUMBERS: [MessageHandler(filters.TEXT, enter_numbers)],
        ENTER_POINTS: [MessageHandler(filters.TEXT, enter_points)],
        CONFIRM: [CallbackQueryHandler(confirm_bet)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
```

## Quy tắc quan trọng
- Handlers gọi application use cases trực tiếp (không qua HTTP)
- Auth qua `telegram_id`: tra `users` table, không dùng JWT
- Admin check: `update.effective_user.id in TELEGRAM_ADMIN_IDS`
- Format tiền: `f"{amount:,.0f} VND"` (dấu phẩy ngăn cách hàng nghìn)
- Timeout ConversationHandler: 5 phút

## Thông báo kết quả (18:35)
`payout_service` gọi `TelegramNotifier.send_user_message()` sau khi settle.
Format: Tóm tắt cược hôm nay + tổng thắng/thua.

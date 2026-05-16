# Telegram Bot Developer Memory - Sicbo

## Ngữ cảnh
Bot Telegram cho Sicbo dùng `python-telegram-bot 20.x` (async PTB v20).
Chạy cùng process với FastAPI qua `asyncio.create_task` trong lifespan.

## Cấu trúc Bot
```
interfaces/telegram_bot/
├── bot.py                     # Application builder, register all handlers
└── handlers/
    ├── start.py               # /start, /help, /register, /lienket
    ├── betting.py             # /bet - ConversationHandler 5 states
    ├── wallet.py              # /balance, /deposit, /withdraw
    ├── results.py             # /ketqua, /lichsu
    └── admin.py               # /pending_withdrawals (admin only)
```

## Commands đã thiết kế
```
/start, /register, /lienket    — Auth flow
/balance, /deposit, /withdraw  — Wallet
/bet                           — Betting ConversationHandler
/ketqua [game_id]              — Results (default: xsmb)
/lichsu                        — Last 5 bets
/help
/pending_withdrawals           — Admin only
```

## Auth trong Bot (không dùng JWT)
```python
user = await user_repo.get_by_telegram_id(update.effective_user.id)
if not user:
    await update.message.reply_text("Bạn chưa đăng ký. Dùng /register")
    return
```

## Admin check
```python
ADMIN_IDS = [int(x) for x in os.environ["TELEGRAM_ADMIN_IDS"].split(",")]
if update.effective_user.id not in ADMIN_IDS:
    await update.message.reply_text("Chỉ admin mới dùng được lệnh này.")
    return
```

## ConversationHandler /bet pattern
```python
CHOOSE_GAME, CHOOSE_TYPE, ENTER_NUMBERS, ENTER_POINTS, CONFIRM = range(5)
# State machine: game → type → numbers → points → confirm/cancel
```

## Format tiền
```python
f"{amount:,.0f} VND"  # ví dụ: 1,125,000 VND
```

## Thông báo tự động (18:35)
Sau settlement, `TelegramNotifier` gửi tóm tắt cho từng user có cược hôm nay.
Format:
```
📊 KẾT QUẢ HÔM NAY
━━━━━━━━━━━━━━━━━
✅ Thắng: 3 lệnh — +375,000 VND
❌ Thua: 2 lệnh — -150,000 VND
💰 Số dư: 1,500,000 VND
```

## Timeout ConversationHandler
5 phút không phản hồi → tự hủy conversation state.

# CLAUDE.md — Sicbo Project

## Tổng quan dự án

**Tên:** Sicbo - Nạp 1 phút rút 1 giây
**Mục đích:** Web app cờ bạc số đề dựa trên kết quả XSMB (Xổ Số Miền Bắc). Mỗi ngày 18:30 hệ thống tự lấy kết quả, tính thắng thua, trả tiền. Người chơi tương tác qua Web hoặc Telegram Bot.

---

## Tech Stack

| Layer | Tech | Deploy |
|---|---|---|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Vercel (free) |
| Backend | Python 3.12 + FastAPI + Clean Architecture | Railway.app |
| Database | PostgreSQL + SQLAlchemy async | Supabase |
| Scheduler | APScheduler 3.x (trong FastAPI process) | Railway |
| Bot | python-telegram-bot 20.x (trong FastAPI process) | Railway |
| Payment | SePay free (bank + MoMo webhook) | SePay cloud |

---

## Kiến trúc - Clean Architecture (Backend)

```
backend/app/
├── domain/            # Layer 1: Business rules, NO external dependencies
│   ├── entities/      # User, Bet, Wallet, GameResult
│   ├── value_objects/ # Money, BetType
│   ├── repositories/  # Abstract interfaces (IUserRepository, etc.)
│   └── games/         # Game plugin system (AbstractGame + GameRegistry)
│       ├── base.py    # AbstractGame interface
│       ├── registry.py
│       └── xsmb/      # XSMBGame (Lô, Đề, Xiên 2, Xiên 3)
│
├── application/       # Layer 2: Use cases
│   ├── use_cases/     # One class per use case
│   └── ports/         # Output port interfaces (INotificationPort, etc.)
│
├── infrastructure/    # Layer 3: DB, external APIs, Telegram
│   ├── database/      # SQLAlchemy models + PostgreSQL repos
│   ├── external/      # XSMB API fetcher, SePay gateway
│   └── notifications/ # Telegram notifier
│
└── interfaces/        # Layer 4: FastAPI routers, Telegram bot, Scheduler
```

**Quy tắc dependency:** `interfaces → application → domain`. Infrastructure implement interfaces của domain. KHÔNG import ngược chiều.

---

## Game Plugin System

Thêm game mới KHÔNG sửa core code. Chỉ cần:
1. Tạo `domain/games/<game_name>/game.py` implement `AbstractGame`
2. `GameRegistry.register(NewGame())`
3. Set `is_active = True`

**Games hiện tại:**
- `xsmb` — Lô 1:75, Đề 1:75, Xiên 2: 1:10, Xiên 3: 1:40
- `bau_cua` — stub (chưa active)
- `duck_race` — stub (chưa active)
- `horse_race` — stub (chưa active)

---

## Quy tắc Game XSMB

- **Cutoff:** 18:10 (server-side, không tin client)
- **Kết quả:** 18:30 (APScheduler gọi XSMB API)
- **Settlement:** 18:35 (tính thắng thua, cộng tiền)
- **Lô:** `all_last2` là LIST có duplicate — "23" xuất hiện 3 lần → thắng 3×75×stake
- **Đề:** chỉ so với 2 số cuối giải Đặc Biệt

---

## API chính

| Endpoint | Mô tả |
|---|---|
| `POST /api/auth/register` | Đăng ký |
| `POST /api/auth/login` | Đăng nhập → JWT |
| `GET /api/games` | Danh sách game + bet types |
| `POST /api/bets` | Đặt cược |
| `POST /api/wallet/deposit/init` | Tạo lệnh nạp |
| `POST /api/webhooks/sepay` | SePay webhook (public) |
| `POST /api/admin/withdrawals/{id}/approve` | Duyệt rút tiền |

---

## Biến môi trường (Backend)

```bash
DATABASE_URL=postgresql+asyncpg://...
JWT_SECRET_KEY=<64 hex chars>
JWT_REFRESH_SECRET_KEY=<64 hex chars>
TELEGRAM_BOT_TOKEN=<from BotFather>
TELEGRAM_ADMIN_IDS=123456789,987654321
TELEGRAM_ADMIN_CHAT_ID=<group or channel ID>
SEPAY_WEBHOOK_SECRET=<from SePay dashboard>
BANK_ACCOUNT_NO=...
BANK_ACCOUNT_NAME=...
BANK_NAME=VietinBank
MOMO_PHONE=...
FRONTEND_URL=https://sicbo.vercel.app
```

---

## Lệnh phát triển

```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
alembic upgrade head                                # Chạy migrations
uvicorn app.interfaces.api.main:app --reload        # Dev server

# Chạy tests
pytest tests/ -v

# Frontend
cd frontend
npm install
npm run dev
```

---

## MCP Tools (qua Telegram)

Claude Code dùng Telegram MCP để:
- Giao task cho team qua Telegram
- Nhận phản hồi khi task hoàn thành
- Hỏi status hiện tại của dự án

Xem `.mcp.json` và `mcp_servers/telegram_mcp.py` để biết cấu hình.

---

## Lưu ý quan trọng

- **Balance changes phải atomic:** Dùng `SELECT FOR UPDATE` + transaction
- **SePay webhook phải verify HMAC** trước khi cộng tiền
- **Cutoff 18:10** enforce server-side, không bao giờ tin client
- **Lô all_last2 là LIST** (có duplicate), KHÔNG phải set
- Telegram bot chạy cùng process FastAPI qua `asyncio.create_task`
- Railway free tier: KHÔNG sleep → APScheduler hoạt động ổn

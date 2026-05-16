# Sicbo — Hướng dẫn chạy project

Tài liệu này giúp bạn dựng và chạy toàn bộ hệ thống Sicbo trên máy local (Windows). Có 3 service chạy song song:

| # | Service | Port | Tech |
|---|---|---|---|
| 1 | PostgreSQL | 5432 | Postgres 14+ |
| 2 | Backend (FastAPI + APScheduler + Telegram bot) | 8000 | Python 3.12 |
| 3 | Frontend (Next.js) | 3000 | Node.js 20+ |

---

## 0. Yêu cầu

- **Windows 10/11**, PowerShell hoặc Git Bash
- **Python 3.12+** — https://python.org
- **Node.js 20+** — đã cài qua winget (`node --version` phải ra v20+)
- **PostgreSQL 14+** — chọn 1 trong 2:
  - Local: cài Postgres trên máy
  - Cloud miễn phí: tạo project Supabase, lấy connection string

---

## 1. Cài Postgres (local) — bỏ qua nếu dùng Supabase

```powershell
winget install -e --id PostgreSQL.PostgreSQL
```

Sau khi cài, mở `pgAdmin` hoặc `psql` tạo database:

```sql
CREATE DATABASE sicbo;
CREATE USER sicbo WITH PASSWORD 'sicbo';
GRANT ALL PRIVILEGES ON DATABASE sicbo TO sicbo;
```

Connection string sẽ là: `postgresql+asyncpg://sicbo:sicbo@localhost:5432/sicbo`

---

## 2. Cấu hình biến môi trường

### 2.1 Tạo `backend/.env`

Copy block sau vào file `backend/.env` và chỉnh giá trị:

```env
# ----- Database -----
DATABASE_URL=postgresql+asyncpg://sicbo:sicbo@localhost:5432/sicbo

# ----- JWT (PHẢI đổi trong production, tối thiểu 64 hex chars) -----
JWT_SECRET_KEY=dev_secret_key_dev_secret_key_dev_secret_key_dev_secret_key_aaaa
JWT_REFRESH_SECRET_KEY=dev_refresh_key_dev_refresh_key_dev_refresh_key_dev_refresh_b

# ----- Telegram Bot (tạo bot qua @BotFather, lấy token) -----
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_IDS=
TELEGRAM_ADMIN_CHAT_ID=

# ----- SePay webhook (lấy từ dashboard.sepay.vn) -----
SEPAY_WEBHOOK_SECRET=

# ----- Bank info để hiển thị cho user khi nạp -----
BANK_ACCOUNT_NO=
BANK_ACCOUNT_NAME=
BANK_NAME=VietinBank
MOMO_PHONE=

# ----- App -----
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
DEBUG=true
```

> Không có Telegram bot / SePay vẫn chạy được — chỉ những tính năng đó bị disabled.

### 2.2 Tạo `frontend/.env.local`

Đã có sẵn:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 3. Chạy Backend

### 3.1 Tạo virtualenv + cài dependencies

```powershell
cd d:\AI\Project_AI\Sicbo\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Apply migrations

```powershell
alembic upgrade head
```

> Nếu lỗi `connection refused`, kiểm tra Postgres đã chạy chưa và `DATABASE_URL` trong `.env` đúng chưa.

### 3.3 Chạy dev server

```powershell
uvicorn app.interfaces.api.main:app --reload --port 8000
```

Health check: http://localhost:8000/health → `{"status":"ok","env":"development"}`

Swagger docs: http://localhost:8000/docs

### 3.4 (Tùy chọn) Chạy tests

```powershell
pytest tests/ -v
```

---

## 4. Chạy Frontend

Mở **terminal mới** (giữ backend đang chạy ở terminal cũ):

```powershell
cd d:\AI\Project_AI\Sicbo\frontend
npm install        # chỉ chạy lần đầu, hoặc khi đổi package.json
npm run dev
```

Mở browser: http://localhost:3000

> Nếu `npm` báo lỗi "running scripts is disabled", chạy PowerShell với:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> rồi mở lại terminal.

---

## 5. Smoke test luồng cơ bản

1. Vào http://localhost:3000 → bấm **Đăng ký**, tạo user
2. Sau đăng ký auto-login → header hiển thị balance `0₫`
3. Vào **Ví → Nạp tiền** → tạo lệnh nạp 100,000 → thấy QR + nội dung CK
4. (Nếu có SePay) chuyển khoản đúng nội dung → vài giây sau balance tăng
5. Vào **Đặt cược → XSMB** → chọn Đề, đánh `23`, stake 10,000 → đặt cược
6. **Lịch sử** hiển thị lệnh pending. 18:30 hệ thống tự lấy kết quả và settle.

---

## 6. Telegram Bot (tuỳ chọn)

1. Mở Telegram, chat với [@BotFather](https://t.me/BotFather) → `/newbot` → lấy token
2. Lấy chat ID admin: chat với [@userinfobot](https://t.me/userinfobot) → copy `Id`
3. Điền vào `backend/.env`:
   ```
   TELEGRAM_BOT_TOKEN=<token từ BotFather>
   TELEGRAM_ADMIN_IDS=<your chat id>
   TELEGRAM_ADMIN_CHAT_ID=<chat id để nhận notification>
   ```
4. Restart backend → bot tự chạy cùng FastAPI process
5. Trong app web vào **Tài khoản → Tạo token liên kết** → vào bot gửi `/link <token>` để link

---

## 7. Cấu trúc thư mục

```
Sicbo/
├── backend/                       # FastAPI + Clean Architecture
│   ├── app/
│   │   ├── domain/               # Entities, games, repositories interfaces
│   │   ├── application/          # Use cases + ports
│   │   ├── infrastructure/       # DB, external APIs, Telegram notifier
│   │   └── interfaces/           # API routers, scheduler, bot handlers
│   ├── migrations/               # Alembic
│   ├── tests/
│   └── requirements.txt
├── frontend/                     # Next.js 14
│   ├── app/                      # App Router pages
│   ├── components/
│   ├── lib/                      # api.ts, store.ts, types.ts, utils.ts
│   └── package.json
├── mcp_servers/                  # Tools Claude dùng để báo Telegram khi làm task
└── CLAUDE.md                     # Tài liệu kiến trúc cho AI
```

---

## 8. Lệnh thường dùng

```powershell
# Backend
cd backend
.venv\Scripts\activate
uvicorn app.interfaces.api.main:app --reload     # dev server
alembic upgrade head                              # apply migration mới
alembic revision --autogenerate -m "msg"          # tạo migration mới
pytest tests/ -v                                  # chạy test

# Frontend
cd frontend
npm run dev                                       # dev server
npm run build                                     # build prod
npm run lint                                      # check lint
npx tsc --noEmit                                  # type check
```

---

## 9. Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|---|---|---|
| `connection refused` khi `alembic upgrade head` | Postgres chưa chạy | Mở Services → start `postgresql-x64-XX` |
| `relation "users" does not exist` | Chưa migrate | `alembic upgrade head` |
| Frontend `Network Error` khi login | Backend chưa chạy hoặc CORS | Check `http://localhost:8000/health` |
| `npm.ps1 cannot be loaded` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Bot không phản hồi `/link` | Token sai hoặc bot chưa chạy | Check log backend, verify `TELEGRAM_BOT_TOKEN` |
| Scheduler không chạy 18:30 | Server timezone sai | App force VN_TZ trong code; xem log backend |

---

## 10. Quy tắc giờ XSMB

- **18:10** — Cutoff: server từ chối mọi lệnh cược sau giờ này (kiểm tra server-side, không tin client)
- **18:30** — APScheduler gọi API xosonhanh.vn lấy kết quả XSMB
- **18:35** — Settlement: tự động tính thắng thua, cộng tiền, gửi Telegram cho user đã link

Game hiện active: chỉ `xsmb`. Các game `bau_cua`, `duck_race`, `horse_race` đang stub (Phase 7).

---

## 11. Deploy nhanh (Phase 8 — chưa làm)

- **Backend**: Railway.app — connect repo, set env vars, deploy. Free tier không sleep.
- **Database**: Supabase — tạo project, copy connection string vào `DATABASE_URL`.
- **Frontend**: Vercel — connect repo nhánh `main`, set `NEXT_PUBLIC_API_BASE_URL` trỏ về Railway URL.
- **SePay**: Cấu hình webhook trỏ về `https://<railway-url>/api/webhooks/sepay`.

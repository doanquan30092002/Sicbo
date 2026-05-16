# Skill: Setup Dev Environment - Sicbo

## Backend Setup

```bash
cd backend

# Tạo virtual env
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Hoặc cmd
.venv\Scripts\activate.bat

# Cài dependencies
pip install -r requirements.txt

# Tạo .env file (copy từ template)
cp .env.example .env
# Sửa .env: DATABASE_URL, JWT secrets, TELEGRAM_BOT_TOKEN, SEPAY_WEBHOOK_SECRET

# Chạy migrations
alembic upgrade head

# Start dev server
uvicorn app.interfaces.api.main:app --reload --port 8000
```

## Frontend Setup (khi bắt đầu Phase 6)

```bash
# Tạo Next.js app
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false --import-alias="@/*"

cd frontend
npx shadcn-ui@latest init  # config tailwind + components.json

# Cài dependencies bổ sung
npm install axios zustand swr sonner react-hook-form @hookform/resolvers zod

# Setup shadcn components hay dùng
npx shadcn-ui@latest add button input card dialog badge table form toast skeleton

# Tạo .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start
npm run dev   # http://localhost:3000
```

## Database (Local PostgreSQL — optional)

Nếu không dùng Supabase mà chạy local:

```bash
# Docker (nhanh nhất)
docker run -d --name sicbo-pg \
  -e POSTGRES_USER=sicbo \
  -e POSTGRES_PASSWORD=sicbo \
  -e POSTGRES_DB=sicbo \
  -p 5432:5432 \
  postgres:16

# .env
DATABASE_URL=postgresql+asyncpg://sicbo:sicbo@localhost:5432/sicbo
```

## Telegram Bot Token

1. Mở @BotFather trên Telegram
2. `/newbot` → đặt tên + username
3. Copy token vào `.env`: `TELEGRAM_BOT_TOKEN=...`
4. Lấy chat_id: gửi tin nhắn cho bot, GET `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Lưu chat_id vào `TELEGRAM_ADMIN_CHAT_ID` và `TELEGRAM_ADMIN_IDS`

## SePay Setup (testing webhook)

```bash
# Expose local backend qua ngrok cho SePay test
ngrok http 8000

# Webhook URL: https://<ngrok-url>.ngrok.io/api/webhooks/sepay
# Set trong SePay dashboard
# Lấy webhook secret từ SePay → .env SEPAY_WEBHOOK_SECRET
```

## Verify setup OK

```bash
# 1. Health check
curl http://localhost:8000/health
# {"status":"ok","env":"development"}

# 2. List games
curl http://localhost:8000/api/games

# 3. Register test user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pwd12345"}'

# 4. Bot ping (Telegram): /start
```

## Troubleshooting

| Lỗi | Giải pháp |
|---|---|
| `ModuleNotFoundError: app` | `set PYTHONPATH=backend` hoặc activate venv |
| `connection refused` (DB) | Check DATABASE_URL, PostgreSQL có chạy không |
| `alembic.util.exc.CommandError: Target database is not up to date` | `alembic upgrade head` |
| Bot không phản hồi | Check `TELEGRAM_BOT_TOKEN`, xem logs FastAPI khi start |
| Webhook 401 | Check `SEPAY_WEBHOOK_SECRET` khớp với SePay dashboard |

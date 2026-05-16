# Skill: Deploy Sicbo

## Backend → Railway

```bash
# 1. Push code lên GitHub
git push origin main

# 2. Railway tự động deploy từ GitHub
# Hoặc manual trigger qua Railway dashboard

# 3. Kiểm tra logs
railway logs --tail
```

**Env vars cần set trên Railway:**
- DATABASE_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY
- TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS, TELEGRAM_ADMIN_CHAT_ID
- SEPAY_WEBHOOK_SECRET
- BANK_ACCOUNT_NO, BANK_ACCOUNT_NAME, BANK_NAME, MOMO_PHONE
- FRONTEND_URL

## Frontend → Vercel

```bash
# Vercel tự deploy khi push lên main
# Hoặc manual:
npx vercel --prod
```

**Env vars cần set trên Vercel:**
- NEXT_PUBLIC_API_URL=https://<railway-url>.up.railway.app

## SePay Webhook

1. Đăng nhập SePay dashboard
2. Vào cài đặt webhook
3. URL: `https://<railway-url>.up.railway.app/api/webhooks/sepay`
4. Method: POST
5. Lưu secret key vào SEPAY_WEBHOOK_SECRET trên Railway

## Database Migration (Supabase)

```bash
cd backend
alembic upgrade head
```

## Kiểm tra sau deploy

1. `GET /health` → 200 OK
2. `POST /api/auth/register` với user test
3. `POST /api/auth/login` → lấy token
4. `GET /api/games` → list games
5. Telegram bot: gửi `/start`
6. SePay: test webhook với curl hoặc SePay test panel

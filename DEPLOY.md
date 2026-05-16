# Sicbo — Hướng dẫn Deploy Production (Phase 8)

Hệ thống chia 3 service deploy độc lập, **free tier** đều OK:

| Service | Nền tảng | Free tier limit |
|---|---|---|
| Database | **Supabase** (PostgreSQL) | 500 MB storage, 2 GB egress/tháng |
| Backend | **Railway.app** | $5 credit/tháng, không sleep |
| Frontend | **Vercel** | 100 GB bandwidth/tháng |

---

## 1. Database — Supabase

1. Truy cập https://supabase.com → **New project**
2. Đặt password mạnh cho `postgres` user, chọn region **Singapore** (gần VN)
3. Sau khi project ready: **Settings → Database → Connection string → URI**
4. Copy connection string, **thay** `postgresql://` thành `postgresql+asyncpg://`
   - Ví dụ: `postgresql+asyncpg://postgres:YOUR_PW@db.xxxxx.supabase.co:5432/postgres`
5. Lưu lại — sẽ dán vào `DATABASE_URL` ở Railway

> Migration sẽ chạy tự động khi backend khởi động lần đầu (Dockerfile + Railway start command).

---

## 2. Backend — Railway

### 2.1 Push code lên GitHub

```bash
cd d:\AI\Project_AI\Sicbo
git init                          # nếu chưa init
git add .
git commit -m "chore: initial commit for deploy"
gh repo create sicbo --private --source . --push   # cần gh CLI
```

### 2.2 Tạo project trên Railway

1. https://railway.app → **New Project → Deploy from GitHub repo**
2. Chọn repo `sicbo`
3. Railway auto-detect monorepo → **Settings → Root Directory** = `backend`
4. **Settings → Build** → builder = Nixpacks (đã config trong `railway.toml`)

### 2.3 Generate JWT secrets

```bash
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(64))"
python -c "import secrets; print('JWT_REFRESH_SECRET_KEY=' + secrets.token_hex(64))"
```

### 2.4 Set environment variables (Railway → Variables)

```env
DATABASE_URL=postgresql+asyncpg://postgres:...@db.xxxxx.supabase.co:5432/postgres
JWT_SECRET_KEY=<64 hex chars vừa tạo>
JWT_REFRESH_SECRET_KEY=<64 hex chars khác>
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=https://<your-app>.vercel.app

# Telegram (tuỳ chọn)
TELEGRAM_BOT_TOKEN=<token từ @BotFather>
TELEGRAM_ADMIN_IDS=<your_telegram_id>
TELEGRAM_ADMIN_CHAT_ID=<group/channel id>

# SePay (tuỳ chọn)
SEPAY_WEBHOOK_SECRET=<từ dashboard.sepay.vn>
BANK_ACCOUNT_NO=<số tk>
BANK_ACCOUNT_NAME=<chủ tk>
BANK_NAME=VietinBank
MOMO_PHONE=<sdt momo>
```

### 2.5 Apply migration lần đầu

Railway sẽ tự deploy. Mở **Deployments → View logs**, đảm bảo thấy:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 20260516_0001, initial
INFO  Khởi động Sicbo API — env=production
```

Nếu start command trong `railway.toml` chưa có `alembic upgrade head`, thêm vào:

```toml
[deploy]
startCommand = "alembic upgrade head && uvicorn app.interfaces.api.main:app --host 0.0.0.0 --port $PORT"
```

### 2.6 Lấy public URL

**Settings → Networking → Generate Domain** → URL dạng `https://sicbo-production.up.railway.app`

Test health:
```bash
curl https://sicbo-production.up.railway.app/health
# → {"status":"ok","env":"production"}
```

---

## 3. Frontend — Vercel

1. https://vercel.com → **Add New → Project → Import** từ GitHub
2. Chọn repo `sicbo`
3. **Root Directory** = `frontend`
4. Framework preset auto-detect = Next.js
5. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://sicbo-production.up.railway.app
   ```
6. **Deploy**

Sau khi deploy xong → URL kiểu `https://sicbo.vercel.app`

### 3.1 Update CORS

Quay lại Railway → **Variables** → update:
```
FRONTEND_URL=https://sicbo.vercel.app
```
→ Railway tự redeploy. Backend sẽ chỉ accept CORS từ domain này khi `ENVIRONMENT=production`.

---

## 4. SePay Webhook

1. Đăng nhập https://dashboard.sepay.vn
2. **Cài đặt → Webhook → Thêm webhook**
3. URL: `https://sicbo-production.up.railway.app/api/webhooks/sepay`
4. Secret: copy từ `SEPAY_WEBHOOK_SECRET` ở Railway
5. Liên kết tài khoản ngân hàng (đúng `BANK_ACCOUNT_NO`)
6. Test bằng cách chuyển khoản 1,000đ với nội dung `NAP001<user_id>` → check Railway log

---

## 5. Telegram Bot

Bot tự chạy cùng FastAPI process (lifespan). Không cần deploy riêng.

Verify:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

Mở Telegram chat với bot → gửi `/start` → bot phản hồi.

---

## 6. Domain riêng (tuỳ chọn)

### Frontend (Vercel)
**Settings → Domains → Add** → trỏ A record `@` về `76.76.21.21` hoặc CNAME `cname.vercel-dns.com`

### Backend (Railway)
**Settings → Networking → Custom Domain** → add `api.yourdomain.com` → set CNAME theo hướng dẫn

---

## 7. CI/CD (GitHub Actions)

Đã có sẵn:
- `.github/workflows/backend-ci.yml` — chạy pytest + ruff + alembic mỗi PR
- `.github/workflows/frontend-ci.yml` — chạy `tsc`, `lint`, `build` mỗi PR

Railway và Vercel đều **auto-deploy khi push lên `main`**, không cần workflow deploy riêng.

---

## 8. Monitoring & Logs

| Service | Logs |
|---|---|
| Railway | Dashboard → Deployments → View Logs (realtime) |
| Vercel | Dashboard → Project → Logs |
| Supabase | Dashboard → Logs Explorer |

Đề xuất thêm:
- **Sentry** cho error tracking (free 5k events/month) — thêm `sentry-sdk[fastapi]` vào requirements
- **UptimeRobot** ping `/health` mỗi 5 phút (free, alert qua email/Telegram)

---

## 9. Checklist trước khi public

- [ ] `JWT_SECRET_KEY` và `JWT_REFRESH_SECRET_KEY` đã đổi sang random 64 hex chars
- [ ] `ENVIRONMENT=production` và `DEBUG=false` ở Railway
- [ ] `FRONTEND_URL` trỏ đúng Vercel domain (CORS sẽ chặn các origin khác)
- [ ] `SEPAY_WEBHOOK_SECRET` đúng với dashboard SePay
- [ ] Đã test nạp tiền real (1,000đ) → balance tăng đúng
- [ ] Đã test đặt cược trước 18:10 và bị từ chối sau 18:10
- [ ] APScheduler chạy đúng VN timezone (check log lúc 18:30)
- [ ] Telegram bot phản hồi `/start`, `/link`, `/balance`
- [ ] Admin có thể approve/reject withdrawal qua bot

---

## 10. Rollback

### Railway
**Deployments → chọn deployment cũ → Redeploy**

### Vercel
**Deployments → chọn deployment cũ → Promote to Production**

### Database
Supabase backup tự động hàng ngày trên free tier (giữ 7 ngày). Restore từ **Database → Backups**.

---

## 11. Chi phí dự kiến (production-grade)

| Service | Free tier đủ cho | Paid khi cần |
|---|---|---|
| Supabase | < 500 MB DB, < 50k user | $25/mo Pro plan |
| Railway | < $5/mo usage (~512 MB RAM 24/7) | pay-as-you-go |
| Vercel | < 100 GB bandwidth | $20/mo Pro |
| SePay | webhook free vĩnh viễn | — |

Ước tính < 1,000 user active: **$0/tháng**. Khi scale: ~$50-70/tháng tổng.

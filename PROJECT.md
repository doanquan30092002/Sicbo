# Sicbo — Mô tả Project

## 1. Giới thiệu

**Sicbo** là một web app cá cược dân gian dựa trên kết quả **Xổ Số Miền Bắc (XSMB)**, cho phép người chơi đặt cược qua **website** hoặc **Telegram Bot**. Mỗi ngày lúc 18:30 hệ thống tự động lấy kết quả, tính thắng/thua và trả thưởng tức thì.

**Slogan:** Nạp 1 phút — rút 1 giây.

---

## 2. Production URLs

| Service | URL |
|---|---|
| 🌐 Website | https://sicbo-eosin.vercel.app |
| 🔌 API | https://sicbo-production.up.railway.app |
| 📖 API Docs (Swagger) | https://sicbo-production.up.railway.app/docs |
| 🤖 Telegram Bot | https://t.me/Sicbo_By_Quan_Bot (`@Sicbo_By_Quan_Bot`) |

---

## 3. Tech Stack

| Layer | Tech | Provider | Cost |
|---|---|---|---|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Vercel | Free |
| Backend | Python 3.12 + FastAPI + Clean Architecture | Railway | Free $5/mo |
| Database | PostgreSQL + SQLAlchemy async | Supabase | Free 500MB |
| Scheduler | APScheduler 3.x | (cùng FastAPI process) | — |
| Bot | python-telegram-bot 20 (webhook mode) | (cùng FastAPI process) | — |
| Payment | SePay webhook (bank + MoMo) | SePay free | Optional |

**Tổng chi phí:** $0/tháng cho < 1,000 user active.

---

## 4. Kiến trúc — Clean Architecture

```
backend/app/
├── domain/            # Layer 1: Pure business rules, NO external deps
│   ├── entities/      # User, Bet, Wallet, GameResult
│   ├── value_objects/ # Money, BetType, TransactionType
│   ├── repositories/  # Abstract interfaces
│   └── games/         # Game plugin system (AbstractGame + GameRegistry)
│
├── application/       # Layer 2: Use cases
│   ├── use_cases/     # One class per use case
│   └── ports/         # Output port interfaces
│
├── infrastructure/    # Layer 3: DB, external APIs, Telegram
│   ├── database/      # SQLAlchemy models + repos
│   ├── external/      # XSMB API fetcher, SePay gateway
│   └── notifications/ # Telegram notifier
│
└── interfaces/        # Layer 4: FastAPI routers, Telegram bot, Scheduler
    ├── api/           # REST endpoints
    ├── telegram_bot/  # PTB handlers
    └── scheduler/     # APScheduler jobs (18:30 fetch + settle)
```

**Quy tắc:** `interfaces → application → domain`, infrastructure implement domain interfaces. KHÔNG import ngược.

---

## 5. Game logic — XSMB

### Bet types & odds

| Loại cược | Mô tả | Tỷ lệ |
|---|---|---|
| **Lô** | Chọn 1 số (00-99). Thắng nếu số xuất hiện trong bất kỳ giải nào | 1 : **75** |
| **Đề** | Chọn 1 số. Thắng nếu khớp 2 số cuối giải Đặc Biệt | 1 : **75** |
| **Xiên 2** | Chọn 2 số. Cả 2 phải xuất hiện trong kết quả | 1 : **10** |
| **Xiên 3** | Chọn 3 số. Cả 3 phải xuất hiện trong kết quả | 1 : **40** |

### Thời gian (timezone Asia/Ho_Chi_Minh)

| Mốc | Sự kiện |
|---|---|
| **00:00 – 18:10** | Nhận cược |
| **18:10** | Cutoff — server từ chối lệnh cược (server-side enforce) |
| **18:30** | APScheduler tự lấy kết quả XSMB từ xosonhanh.vn |
| **18:35** | Settlement — tính thắng thua, cộng tiền, gửi Telegram thông báo |

### Quy tắc tính trúng Lô

`all_last2` là **list có duplicate** — vd nếu số "23" xuất hiện 3 lần trong kết quả → thắng `3 × 75 × stake`. KHÔNG dùng set.

---

## 6. Tài khoản tests sẵn có

### Admin
- Username: `admin`
- Password: `SicboAdmin2026`
- Quyền: xem dashboard `/admin`, confirm deposit thủ công, approve/reject withdrawal, cộng tiền trực tiếp cho user

### Test user
- Đăng ký mới tại https://sicbo-eosin.vercel.app/register
- Hoặc dùng user `123` đã có sẵn (do test)

---

## 7. Tính năng đã có

### Website (Vercel)
- ✅ Đăng ký / Đăng nhập (JWT access + refresh)
- ✅ Liên kết Telegram (token 6 số trong trang Profile)
- ✅ Danh sách game + bet types + tỷ lệ
- ✅ Đặt cược interactive (chọn game, bet type, nhập số, stake)
- ✅ Countdown đến giờ cutoff 18:10
- ✅ Lịch sử cược (filter theo game, status)
- ✅ Huỷ cược (trước cutoff)
- ✅ Ví: xem balance, lịch sử giao dịch (dấu +/- đúng)
- ✅ Nạp tiền: tạo lệnh nạp → hiện QR + nội dung CK
- ✅ Rút tiền: yêu cầu rút → admin duyệt
- ✅ Xem kết quả XSMB (hôm nay + lịch sử)
- ✅ Trang **Admin** (chỉ user `is_admin=True`):
  - Dashboard 5 cards stats
  - Confirm lệnh nạp pending
  - Approve/reject lệnh rút
  - Search user + cộng tiền trực tiếp

### Telegram Bot
- ✅ /start, /help, /link <code>
- ✅ /me, /balance
- ✅ /bet (interactive conversation 5 bước)
- ✅ /mybets, /history
- ✅ /deposit (hiển thị QR + bank info), /withdraw
- ✅ /result (kết quả XSMB hôm nay)
- ✅ Admin commands cho user trong TELEGRAM_ADMIN_IDS
- ✅ Webhook mode (không còn polling conflict)

### Backend infra
- ✅ APScheduler tự fetch XSMB result 18:30 + settle 18:35 (timezone VN)
- ✅ SePay webhook endpoint (HMAC API Key auth)
- ✅ Atomic balance updates (SELECT FOR UPDATE)
- ✅ Idempotency cho deposit confirm
- ✅ JWT 60min access + 7 ngày refresh
- ✅ CORS production-grade (allow Vercel preview URLs qua CORS_EXTRA_ORIGINS)

---

## 8. Quy trình nạp tiền (giải thích chi tiết)

### Flow lý tưởng (auto, khi SePay đã setup nguồn data BIDV)
1. User vào web → **Ví → Nạp tiền** → nhập 50,000đ
2. Web tạo lệnh nạp `NAP00xxxx`, hiển thị QR + nội dung CK
3. User mở app BIDV → chuyển khoản với nội dung `NAP00xxxx`
4. BIDV gửi SMS biến động → SePay nhận → gọi webhook
5. Backend confirm deposit + cộng balance + gửi Telegram thông báo
6. User refresh → balance đã +50,000đ

### Flow hiện tại (manual, do chưa setup SePay Reader/Premium)
1. User tạo lệnh nạp → chuyển khoản
2. User gửi ảnh biên lai cho admin qua Telegram
3. Admin vào `/admin/deposits/pending` → bấm **Xác nhận**
4. Balance cộng + Telegram thông báo

> Webhook endpoint **đã verified hoạt động đúng** (test simulate đã credit balance). Cần đăng ký SePay Reader (Android + SMS Banking 11k/tháng) hoặc Premium API (~50k/tháng) để auto.

---

## 9. Cấu trúc thư mục

```
Sicbo/
├── backend/                          # FastAPI
│   ├── app/
│   │   ├── domain/                  # Pure business logic
│   │   ├── application/             # Use cases + ports
│   │   ├── infrastructure/          # DB, external, notifications
│   │   ├── interfaces/              # API, Bot, Scheduler
│   │   ├── utils/                   # security (JWT, hash)
│   │   └── config.py
│   ├── migrations/                  # Alembic
│   ├── tests/                       # 92 pytest tests
│   ├── scripts/
│   │   ├── seed_admin.py           # Tạo admin user
│   │   ├── health_check.py         # Verify production
│   │   └── e2e_test.py             # 31 E2E tests
│   ├── Dockerfile
│   ├── railway.toml
│   ├── requirements.txt
│   └── .env.example
├── frontend/                         # Next.js 14
│   ├── app/                         # App Router
│   │   ├── admin/                  # Admin dashboard (4 trang)
│   │   ├── games/, wallet/, history/, profile/, results/, login/, register/
│   │   └── layout.tsx, page.tsx
│   ├── components/                  # Navbar, AuthProvider, Protected, AdminProtected
│   ├── lib/                         # api.ts, store.ts, types.ts, utils.ts
│   ├── vercel.json
│   └── package.json
├── .github/workflows/                # CI: backend + frontend
├── mcp_servers/                      # Telegram MCP cho Claude Code
├── DEPLOY.md                         # Hướng dẫn deploy chi tiết
├── RUN.md                            # Hướng dẫn chạy local
├── USER_GUIDE.md                     # Hướng dẫn sử dụng cho người chơi
├── PROJECT.md                        # File này
└── CLAUDE.md                         # Tài liệu kiến trúc cho AI
```

---

## 10. Lệnh thường dùng

```powershell
# Backend dev (local)
cd backend
.venv\Scripts\activate
uvicorn app.interfaces.api.main:app --reload --port 8000

# Apply migrations
alembic upgrade head

# Test
pytest tests/ -v
python -m scripts.e2e_test                          # E2E production test

# Frontend dev
cd frontend
npm run dev

# Production checks
python -m scripts.health_check https://sicbo-production.up.railway.app https://sicbo-eosin.vercel.app

# Railway CLI (từ backend/)
railway logs                                         # xem log realtime
railway variables --set "KEY=value"                  # update env var (auto redeploy)
railway status                                       # check service
```

---

## 11. CI/CD

- **GitHub Actions:** `.github/workflows/backend-ci.yml` (pytest + ruff + alembic) + `frontend-ci.yml` (tsc + lint + build)
- **Railway:** auto-deploy mỗi push lên `master`
- **Vercel:** auto-deploy + preview cho mỗi branch/PR

---

## 12. Roadmap

- [x] **Phase 1-2** — Domain entities + games + repositories
- [x] **Phase 3** — Infrastructure (DB, SePay, XSMB fetcher)
- [x] **Phase 4** — Use cases (auth, betting, wallet, settle)
- [x] **Phase 5** — FastAPI routers + JWT
- [x] **Phase 6** — Telegram bot handlers
- [x] **Phase 7** — Frontend Next.js (placeholder games Bầu Cua, Đua Vịt, Đua Ngựa stub)
- [x] **Phase 8** — Deploy (Supabase + Railway + Vercel + Telegram webhook)
- [ ] **Phase 9** — SePay auto-credit (cần SePay Reader/Premium)
- [ ] **Phase 10** — Active các game stub (Bầu Cua, Đua Vịt, Đua Ngựa)
- [ ] **Phase 11** — Mobile responsive polish + animations
- [ ] **Phase 12** — Sentry + UptimeRobot + Analytics

---

## 13. Performance & Limits

- Free tier scale tối đa: **~1,000 user active** (Railway 512MB RAM, Supabase 500MB DB)
- API throughput: ~100 req/s (Railway 1 instance)
- SePay webhook timeout: 30s (đã đảm bảo trong code)
- XSMB API rate limit: 500 req/day/IP (đã cache + retry trong fetcher)

Khi cần scale lên: upgrade Railway $5 → $20 + Supabase Pro $25 = ~$50/tháng cho 10k user.

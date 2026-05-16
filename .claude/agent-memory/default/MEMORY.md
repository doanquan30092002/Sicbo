# Default Agent Memory - Sicbo Project

## Dự án
**Tên:** Sicbo - Nạp 1 phút rút 1 giây
**Tech:** Python 3.12 + FastAPI (Clean Architecture) / Next.js 14 / PostgreSQL Supabase / Railway + Vercel

## Kiến trúc Backend (4 layers)
```
domain/ → application/ → infrastructure/ → interfaces/
```
- `domain/games/` — Game Plugin: AbstractGame + GameRegistry
- `application/use_cases/` — One class per use case
- `infrastructure/` — DB repos, XSMB API, SePay, Telegram notifier
- `interfaces/api/` & `interfaces/telegram_bot/` & `interfaces/scheduler/`

## Quy tắc quan trọng
- Cutoff XSMB: **18:10** (server-side trong PlaceBet)
- Kết quả XSMB: **18:30** (APScheduler gọi API)
- `all_last2` là **LIST có duplicate** cho Lô (không phải set)
- Balance changes: **SELECT FOR UPDATE** + atomic transaction
- SePay webhook: verify **HMAC-SHA256** trước khi credit
- Decimal cho tất cả money

## Games
- `xsmb` — ACTIVE: Lô 1:75, Đề 1:75, Xiên 2 1:10, Xiên 3 1:40
- `bau_cua`, `duck_race`, `horse_race` — STUB (is_active=False)

## Thêm game mới
1. Tạo `domain/games/<id>/game.py` implement `AbstractGame`
2. `GameRegistry.register(NewGame())`
3. `is_active = True`

## Deploy
- Backend: Railway.app (free $5 credit)
- Frontend: Vercel (free)
- DB: Supabase PostgreSQL (500MB free)
- Payment: SePay free webhook

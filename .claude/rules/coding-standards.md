# Coding Standards - Sicbo Project

## Python (Backend)

- Python 3.12+, type hints bắt buộc trên tất cả function signatures
- Pydantic v2 cho schemas, dataclasses cho domain entities
- Async/await throughout — KHÔNG dùng synchronous DB calls
- Tên file: `snake_case.py`, tên class: `PascalCase`, tên hàm/biến: `snake_case`
- Decimal cho tất cả money calculations — KHÔNG dùng float

## Clean Architecture Rules

- `domain/` KHÔNG được import từ `application/`, `infrastructure/`, hoặc `interfaces/`
- `application/` KHÔNG được import từ `infrastructure/` hoặc `interfaces/`
- `infrastructure/` implement interfaces của `domain/repositories/` và `application/ports/`
- Use cases nhận dependencies qua constructor injection (không import trực tiếp)

## Database

- Tất cả balance changes phải dùng `SELECT FOR UPDATE` + transaction
- KHÔNG bao giờ cộng/trừ balance ngoài `WalletRepository`
- Index bắt buộc: `bets(game_id, draw_date, status)`, `deposits(transfer_content)`, `users(telegram_id)`

## Security

- Verify HMAC-SHA256 trước khi xử lý SePay webhook
- Cutoff time (18:10) enforce server-side trong `PlaceBet` use case
- JWT secret keys tối thiểu 64 chars
- KHÔNG log password hash hoặc JWT tokens

## Game Logic

- `all_last2` cho Lô phải là LIST có duplicate (không phải set)
- Mỗi game implement `AbstractGame` trong `domain/games/`
- Unit test bắt buộc cho `evaluate_bet()` của mỗi bet type

## TypeScript (Frontend)

- Next.js 14 App Router, TypeScript strict mode
- Axios instance với JWT interceptor trong `lib/api.ts`
- Zustand cho auth state
- Cutoff countdown (18:10) là UI-only, không tin vào client-side check

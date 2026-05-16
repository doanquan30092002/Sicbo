# Security Rules - Sicbo Project

## Critical Security Checks

### SePay Webhook
- LUÔN verify HMAC-SHA256 signature trước khi credit balance
- Nếu signature invalid → return 400, log, KHÔNG process
- Idempotent: check `sepay_transaction_id` đã tồn tại trước khi cộng tiền

### Balance Operations
- LUÔN dùng `SELECT FOR UPDATE` khi cập nhật balance
- LUÔN ghi transaction record cùng lúc với balance change
- KHÔNG bao giờ cộng/trừ trực tiếp ngoài `WalletRepository.update_balance()`

### JWT
- Access token TTL: 60 phút
- Refresh token TTL: 7 ngày
- `JWT_SECRET_KEY` phải >= 64 hex chars
- KHÔNG store tokens trong localStorage (dùng httpOnly cookie nếu có thể)

### Betting Cutoff
- Server-side check trong `PlaceBet.execute()`: so sánh `datetime.now(VN_TZ)` với `game.cutoff_time`
- KHÔNG trust client-side countdown
- Return 422 với message rõ ràng nếu đã quá giờ

### Input Validation
- Validate số cược (00-99) server-side trong `AbstractGame.validate_bet()`
- Validate amount > 0 và <= user.balance
- Sanitize tất cả user input trước khi store

### Admin Endpoints
- `/api/admin/*` yêu cầu `is_admin = True` trong JWT
- Telegram admin commands check `telegram_id in TELEGRAM_ADMIN_IDS`

## KHÔNG được làm

- Log password, JWT tokens, SEPAY_WEBHOOK_SECRET
- Commit file `.env` lên git
- Disable CORS hoàn toàn (chỉ allow FRONTEND_URL)
- Trust client-provided `user_id` (luôn lấy từ JWT)

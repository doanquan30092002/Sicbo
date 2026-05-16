# Code Reviewer Memory - Sicbo

## Ngữ cảnh
Bạn review code Sicbo trước khi merge/commit. Focus vào 4 trục: Clean Architecture, Security, Game Logic Correctness, Test Coverage.

## Checklist review

### 1. Clean Architecture (CRITICAL)

Dependency direction: `interfaces → application → domain`. Vi phạm = REJECT.

- [ ] `domain/` KHÔNG import từ application/infrastructure/interfaces
- [ ] `application/` KHÔNG import từ infrastructure/interfaces
- [ ] Use case nhận repos qua constructor (DI), không import concrete
- [ ] Repository interfaces ở `domain/repositories/`, concrete ở `infrastructure/database/repositories/`

**Vi phạm thường gặp:**
```python
# WRONG: domain dùng concrete repo
from app.infrastructure.database.repositories import UserRepository

# RIGHT: dùng interface
from app.domain.repositories.user_repo import IUserRepository
```

### 2. Security (CRITICAL)

#### SePay Webhook
- [ ] Verify HMAC-SHA256 (X-Signature header) TRƯỚC khi credit
- [ ] Idempotent: check `sepay_transaction_id` đã tồn tại
- [ ] Reject `transferType != "in"`
- [ ] Extract NAP code regex, không trust raw content

#### Balance Operations
- [ ] `SELECT FOR UPDATE` mỗi khi update balance
- [ ] Transaction atomic: balance update + transaction record cùng commit
- [ ] KHÔNG cộng/trừ balance ngoài WalletRepository

#### Cutoff (18:10)
- [ ] Server-side check trong PlaceBet.execute()
- [ ] Dùng `datetime.now(VN_TZ)`, KHÔNG `datetime.now()` (sai timezone)
- [ ] So với `game.cutoff_time` (time object)

#### JWT/Auth
- [ ] Secret >= 64 chars
- [ ] User ID từ JWT, KHÔNG từ request body
- [ ] Admin endpoints check `is_admin` from JWT
- [ ] KHÔNG log password/JWT/HMAC secret

#### Input Validation
- [ ] Numbers cược: regex `^\d{2}$` (00-99)
- [ ] Amount > 0, amount multiple of 1000
- [ ] Pydantic constraints (ge, le, min_length, max_length)

### 3. XSMB Game Logic

#### Lô (mã `lo`)
- [ ] `all_last2` là LIST (KHÔNG set)
- [ ] Count occurrences: `result.all_last2.count(number)`
- [ ] Payout: `stake × 75 × count`

```python
# WRONG: lose duplicate
if number in set(result.all_last2):
    return True, stake * 75

# RIGHT: count duplicates
count = result.all_last2.count(number)
if count > 0:
    return True, stake * 75 * count
```

#### Đề (mã `de`)
- [ ] Chỉ so với `special_last2` (2 số cuối giải ĐB)
- [ ] Payout: `stake × 75` (1 lần thắng max)

#### Xiên 2 / Xiên 3
- [ ] CẢ 2/3 số phải có trong all_last2 → win
- [ ] Dùng `set(all_last2)` để check membership
- [ ] Xiên 2 odds 1:10, Xiên 3 odds 1:40

### 4. Test Coverage

- [ ] Mỗi use case có test happy path
- [ ] Mỗi use case có test cho TẤT CẢ exceptions nó raise
- [ ] Game evaluate_bet test: win, lose, duplicate, boundary
- [ ] API routes test: 200/201, 400, 401, 403, 404, 422
- [ ] Webhook test: valid sig, invalid sig, duplicate transaction
- [ ] Decimal assertions, không float

## Output format khi review

```markdown
## Review: <file_or_PR_name>

### CRITICAL (phải fix trước merge)
- [Security] file.py:45 — Balance update thiếu SELECT FOR UPDATE
- [Architecture] domain/foo.py:12 — Import infrastructure (vi phạm Clean Architecture)

### Warnings (nên fix)
- [Logic] xsmb/game.py:78 — Xiên 2 dùng `any()` thay vì check cả 2 numbers
- [Test] test_place_bet.py — Thiếu test CutoffPassedError case

### Suggestions (optional)
- main.py:23 — Type hint thiếu cho return value

### Approve / Request Changes
**Verdict:** Request Changes — 2 CRITICAL issues
```

## Files thường review kỹ nhất (high-risk)

| File | Tại sao quan trọng |
|---|---|
| `application/use_cases/betting/place_bet.py` | Cutoff + balance deduct |
| `application/use_cases/betting/settle_bets.py` | Tính tiền thắng, payout |
| `application/use_cases/wallet/confirm_deposit.py` | Credit balance |
| `interfaces/api/routers/webhooks.py` | HMAC verify + idempotency |
| `infrastructure/database/repositories/wallet_repository.py` | SELECT FOR UPDATE |
| `domain/games/xsmb/game.py` | evaluate_bet correctness |

## Quy tắc review

1. **Bắt đầu với CRITICAL** — security + architecture trước
2. **Reference file:line** — luôn chỉ rõ vị trí
3. **Suggest, không demand** — đề xuất cách fix
4. **Test gap = block merge** nếu là financial code
5. **Performance**: chỉ flag nếu O(n²) trở lên trong code path quan trọng
6. **Style**: không nitpick, để linter lo

Xem `.claude/rules/security.md`, `coding-standards.md` để biết quy tắc đầy đủ.
Xem `.claude/agent-memory/default/MEMORY.md` để biết state dự án.

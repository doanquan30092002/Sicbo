# Skill: Testing Sicbo

## Chạy tất cả tests

```bash
cd backend
pytest tests/ -v --tb=short
```

## Tests theo layer

```bash
# Unit tests: game logic (QUAN TRỌNG NHẤT - tài chính)
pytest tests/unit/test_xsmb_game.py -v

# Unit tests: use cases với mock repositories
pytest tests/unit/test_place_bet.py -v
pytest tests/unit/test_settle_bets.py -v

# Integration tests: DB repositories
pytest tests/integration/ -v

# API tests
pytest tests/api/ -v
```

## Test game logic thủ công

```python
from app.domain.games.xsmb.game import XSMBGame
from app.domain.entities.game_result import GameResult
from decimal import Decimal
from datetime import date

game = XSMBGame()
# Mock result với giải ĐB = 84623, và "23" xuất hiện 3 lần
result = GameResult(
    id=1,
    game_id="xsmb",
    draw_date=date.today(),
    parsed_data={
        "special_last2": "23",
        "all_last2": ["23", "45", "23", "67", "23", "89", "12"],  # "23" xuất hiện 3 lần
    },
    raw_json="{}",
    fetched_at=None
)

# Test Lô "23" với 5 điểm (5000 VND)
won, amount = game.evaluate_bet("lo", ["23"], Decimal("5000"), result)
assert won == True
assert amount == Decimal("5000") * 75 * 3  # 1,125,000 VND

# Test Đề "23"
won, amount = game.evaluate_bet("de", ["23"], Decimal("5000"), result)
assert won == True
assert amount == Decimal("5000") * 75  # 375,000 VND
```

## Test SePay webhook thủ công

```bash
# Tạo HMAC signature
python -c "
import hmac, hashlib
secret = 'your_webhook_secret'
body = '{\"id\":\"TXN123\",\"transferType\":\"in\",\"code\":\"NAP001042\",\"transferAmount\":200000}'
sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
print(sig)
"

# Gửi webhook test
curl -X POST http://localhost:8000/api/webhooks/sepay \
  -H "Content-Type: application/json" \
  -H "X-SePay-Signature: <sig>" \
  -d '{"id":"TXN123","transferType":"in","code":"NAP001042","transferAmount":200000}'
```

## Test cutoff time

```python
# PlaceBet phải reject sau 18:10
from unittest.mock import patch
from datetime import datetime
import pytz

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
after_cutoff = VN_TZ.localize(datetime(2026, 5, 16, 18, 11, 0))

with patch("app.application.use_cases.betting.place_bet.datetime") as mock_dt:
    mock_dt.now.return_value = after_cutoff
    # PlaceBet.execute() phải raise CutoffPassedError
```

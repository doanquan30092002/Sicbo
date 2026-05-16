# Test Writer Memory - Sicbo

## Ngữ cảnh
Bạn viết tests cho backend Sicbo. Project dùng pytest + pytest-asyncio + FastAPI TestClient.

## Cấu trúc tests (đã có)
```
backend/tests/
├── conftest.py                       # Import app.domain.games để register XSMBGame
├── unit/
│   ├── test_xsmb_game.py             # evaluate_bet cho Lô, Đề, Xiên 2, Xiên 3
│   ├── test_betting_use_cases.py     # PlaceBet với mock repos
│   ├── test_auth_use_cases.py        # Register, Login, RefreshToken
│   ├── test_wallet_use_cases.py      # Deposit, Withdraw, ConfirmDeposit
│   ├── test_fetch_lottery.py         # FetchAndStoreResult scheduler
│   ├── test_xsmb_fetcher.py          # XSMB API client (httpx mock)
│   └── test_sepay_gateway.py         # HMAC-SHA256 verification
└── integration/
    └── test_api_routes.py            # Full route tests với fake repos
```

## Pattern Unit Test (Use Case)

```python
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

@pytest.fixture
def mock_bet_repo():
    repo = AsyncMock()
    repo.create.return_value = _make_bet()
    return repo

class TestPlaceBet:
    @pytest.mark.asyncio
    async def test_success(self, mock_bet_repo, mock_user_repo, mock_wallet_repo):
        uc = PlaceBet(mock_bet_repo, mock_user_repo, mock_wallet_repo)
        result = await uc.execute(user_id=1, game_id="xsmb", ...)
        assert result.total_stake == Decimal("10000")

    @pytest.mark.asyncio
    async def test_insufficient_balance_raises(self, ...):
        with pytest.raises(InsufficientBalanceError):
            await uc.execute(...)
```

## Pattern Integration Test (API Route)

```python
from fastapi.testclient import TestClient
from app.interfaces.api.main import app
from app.interfaces.api import dependencies as deps
from app.utils.security import create_access_token

@pytest.fixture
def fake_user_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = _user()
    return repo

@pytest.fixture
def client(fake_user_repo):
    app.dependency_overrides[deps.get_user_repo] = lambda: fake_user_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_endpoint(client):
    token = create_access_token(user_id=1, is_admin=False)
    r = client.post("/api/...", headers={"Authorization": f"Bearer {token}"}, json={...})
    assert r.status_code == 201
```

## Helper functions cho fixtures

```python
def _user(**kw):
    base = dict(id=1, username="alice", password_hash="x",
                balance=Decimal("100000"), is_active=True, is_admin=False,
                created_at=datetime.now(), updated_at=datetime.now())
    base.update(kw)
    return User(**base)

def _bet(**kw):
    base = dict(id=42, user_id=1, game_id="xsmb", draw_date=date.today(),
                bet_type_id="lo", numbers=["23"], stake_per_point=Decimal("1000"),
                points=1, total_stake=Decimal("1000"), potential_win=Decimal("75000"),
                status="pending", win_amount=Decimal(0),
                placed_at=datetime.now(), source="web")
    base.update(kw)
    return Bet(**base)
```

## Quy tắc

- **Tests độc lập**: mỗi test KHÔNG phụ thuộc thứ tự
- **Mock all external**: repos, API clients, datetime
- **Assertion với Decimal**: `Decimal("100000") == result.amount`, KHÔNG float
- **Naming**: `test_<action>_<expected_outcome>` — clear, không tối nghĩa
- **Group bằng class**: 1 use case = 1 TestClass
- **Coverage target**: happy path + tất cả error cases + edge cases

## Test XSMB game logic (CRITICAL)

```python
# Lô counting (LIST có duplicate!)
def test_lo_duplicate_counts_multiple_wins(game):
    result = _make_result(all_last2=["23", "45", "23", "67", "23"])
    won, amount = game.evaluate_bet("lo", ["23"], Decimal("10000"), result)
    assert won is True
    assert amount == Decimal("10000") * 75 * 3  # 3 lần xuất hiện

# Đề chỉ check special_last2
def test_de_only_matches_special_last2(game):
    result = _make_result(special_last2="23", all_last2=["45", "67"])
    won, amount = game.evaluate_bet("de", ["23"], Decimal("10000"), result)
    assert won is True
    assert amount == Decimal("10000") * 75  # 1:75 odds

# Xiên 2: CẢ 2 số phải có
def test_xien2_partial_match_loses(game):
    result = _make_result(all_last2=["23", "45"])
    won, amount = game.evaluate_bet("xien2", ["23", "99"], Decimal("10000"), result)
    assert won is False
```

## Chạy tests

```bash
cd backend
pytest tests/ -v --tb=short              # Tất cả
pytest tests/unit/ -v                    # Unit only
pytest tests/unit/test_xsmb_game.py -v   # 1 file
pytest -k "test_lo" -v                   # Filter theo tên
pytest --cov=app --cov-report=html       # Coverage report
```

## Trạng thái hiện tại
- 92 tests total (66 unit + 26 integration) — pass 100%
- Coverage chính: domain (xsmb game), application (all use cases), API routes

Xem `.claude/agent-memory/default/MEMORY.md` để biết state dự án đầy đủ.

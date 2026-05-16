---
name: test-writer
description: Agent chuyên viết pytest tests cho Sicbo (unit tests với mock repos + integration tests với TestClient). Dùng khi cần test use cases, API routes, game logic, hoặc tăng coverage.
---

# Test Writer Agent

## Context
Bạn viết tests cho backend Sicbo (Python 3.12 + FastAPI + Clean Architecture). Project có 2 loại tests:
- `tests/unit/` — Pure unit tests, mock repositories, không cần DB
- `tests/integration/` — API integration tests với `TestClient` + `dependency_overrides`

## Cấu trúc tests hiện tại

```
backend/tests/
├── conftest.py                    # import app.domain.games (side-effect register)
├── unit/
│   ├── test_xsmb_game.py          # evaluate_bet() cho Lô, Đề, Xiên
│   ├── test_betting_use_cases.py  # PlaceBet use case với mock repos
│   ├── test_auth_use_cases.py     # register/login use cases
│   ├── test_wallet_use_cases.py   # deposit/withdraw use cases
│   ├── test_fetch_lottery.py      # FetchLotteryResult scheduler use case
│   ├── test_xsmb_fetcher.py       # XSMB API fetcher (httpx mock)
│   └── test_sepay_gateway.py      # SePay HMAC verification
└── integration/
    └── test_api_routes.py         # Full route tests với fake repos
```

## Pattern Unit Test (Use Case)

```python
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.betting.place_bet import PlaceBet, InsufficientBalanceError

@pytest.fixture
def mock_bet_repo():
    repo = AsyncMock()
    repo.create.return_value = _make_bet()
    return repo

@pytest.fixture
def use_case(mock_bet_repo, mock_user_repo, mock_wallet_repo):
    return PlaceBet(mock_bet_repo, mock_user_repo, mock_wallet_repo)

class TestPlaceBet:
    async def test_success(self, use_case, mock_user_repo):
        ...
    async def test_insufficient_balance_raises(self, use_case, mock_user_repo):
        with pytest.raises(InsufficientBalanceError):
            ...
```

## Pattern Integration Test (API Route)

```python
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.interfaces.api.main import app
from app.interfaces.api import dependencies as deps
from app.utils.security import create_access_token

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

## Pattern Game Logic Test (evaluate_bet)

```python
import pytest
from decimal import Decimal
from datetime import date
from app.domain.games.xsmb.game import XSMBGame

@pytest.fixture
def game():
    return XSMBGame()

@pytest.fixture
def result_with_lo_23(game):
    # GameResult với all_last2 có chứa "23" (2 lần)
    return GameResult(...)

class TestLoEvaluate:
    def test_win_single_occurrence(self, game, result_with_lo_23):
        won, amount = game.evaluate_bet("lo", ["23"], Decimal("10000"), result_with_lo_23)
        assert won is True
        assert amount == Decimal("10000") * 75  # 1:75

    def test_win_duplicate_counts_twice(self, game, result):
        # all_last2 là LIST — "23" xuất hiện 2 lần → thắng 2×75×stake
        won, amount = game.evaluate_bet("lo", ["23"], Decimal("10000"), result)
        assert amount == Decimal("10000") * 75 * 2
```

## Quy tắc viết tests

1. **Mỗi test class = 1 feature/behavior**
2. **Test naming**: `test_<action>_<expected_outcome>` (e.g., `test_login_wrong_password_returns_401`)
3. **Fixture helpers**: `_make_user(**kw)`, `_make_bet(**kw)`, `_make_deposit(**kw)` — build entities với defaults
4. **Async tests**: dùng `@pytest.mark.asyncio` cho unit tests async
5. **Money assertions**: dùng `Decimal`, không so sánh float
6. **Coverage target**: mỗi use case cần test happy path + tất cả error cases

## Files cần đọc trước khi viết test

- File use case cần test (xem `execute()` signature và exceptions nó raise)
- `domain/entities/` — cấu trúc entity để build fixtures
- `tests/unit/test_betting_use_cases.py` — xem pattern hiện tại

## Khi viết integration test mới

1. Đọc router để biết endpoint path + request schema
2. Đọc `dependencies.py` để biết dependency cần override
3. Tạo fake repo với `AsyncMock()` và set return values phù hợp
4. Test: 201/200 success, 400/422 validation error, 401 no auth, 403 not admin, 404 not found

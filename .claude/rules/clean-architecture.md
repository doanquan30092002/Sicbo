# Clean Architecture Rules - Sicbo Project

## Dependency Direction (BẮT BUỘC)

```
interfaces → application → domain
                ↑
        infrastructure (implement domain interfaces)
```

**Quy tắc 1 chiều**: chỉ import vào trong, không bao giờ ngược ra ngoài.

## Layer Boundaries

### Layer 1: `domain/` (Innermost)

**Được phép import:** Chỉ stdlib + Pydantic
**KHÔNG được import:** `application/`, `infrastructure/`, `interfaces/`, FastAPI, SQLAlchemy, httpx

**Contains:**
- `entities/` — dataclasses thuần
- `value_objects/` — Money, BetType enum
- `repositories/` — Abstract interfaces (IUserRepository, IBetRepository...)
- `games/` — AbstractGame + GameRegistry + concrete games

### Layer 2: `application/`

**Được phép import:** `domain/` + stdlib
**KHÔNG được import:** `infrastructure/`, `interfaces/`

**Contains:**
- `use_cases/<module>/<UseCase>.py` — Một class mỗi use case
- `ports/` — Output port interfaces (INotificationPort, IPaymentGateway...)

**Pattern use case:**
```python
class PlaceBet:
    def __init__(
        self,
        bet_repo: IBetRepository,        # interface từ domain
        user_repo: IUserRepository,
        wallet_repo: IWalletRepository,
    ):
        self._bet_repo = bet_repo
        ...

    async def execute(self, user_id: int, ...) -> Bet:
        # business logic + dùng repos qua interface
```

### Layer 3: `infrastructure/`

**Được phép import:** `domain/`, `application/` (chỉ ports/), stdlib, external libs (SQLAlchemy, httpx)
**KHÔNG được import:** `interfaces/`

**Contains:**
- `database/models/` — SQLAlchemy ORM models
- `database/repositories/` — Concrete repository implementations
- `external/` — XSMB fetcher, SePay gateway (implement application ports)
- `notifications/` — Telegram notifier

### Layer 4: `interfaces/` (Outermost)

**Được phép import:** TẤT CẢ layers
**Trách nhiệm:** Wire dependencies, expose API/CLI/Bot

**Contains:**
- `api/` — FastAPI routers + schemas + dependencies
- `telegram_bot/` — PTB handlers
- `scheduler/` — APScheduler jobs

## Vi phạm phổ biến (REJECT khi review)

### ❌ Domain import infrastructure
```python
# domain/games/xsmb/game.py
from app.infrastructure.database.models import GameResultModel  # WRONG!
```
**Fix**: Dùng entity `domain/entities/game_result.py`, không phải ORM model

### ❌ Application gọi DB trực tiếp
```python
# application/use_cases/betting/place_bet.py
from sqlalchemy import select  # WRONG!
result = await session.execute(select(BetModel)...)
```
**Fix**: Gọi qua `IBetRepository.create()` interface

### ❌ Use case import FastAPI
```python
# application/use_cases/auth/login_user.py
from fastapi import HTTPException  # WRONG!
```
**Fix**: Use case raise custom exception (`InvalidCredentialsError`); router catch và convert sang HTTPException

### ❌ Repository concrete trong constructor
```python
class PlaceBet:
    def __init__(self):
        self.bet_repo = BetRepository(session)  # WRONG! Concrete class
```
**Fix**: Nhận interface qua DI từ FastAPI `Depends()`

## Cách verify

```bash
# Check imports trong domain layer
grep -r "from app.infrastructure" backend/app/domain/    # Phải empty
grep -r "from app.interfaces" backend/app/domain/        # Phải empty
grep -r "from app.application" backend/app/domain/       # Phải empty

# Check application không import infrastructure
grep -r "from app.infrastructure" backend/app/application/  # Phải empty (trừ ports/)
grep -r "from app.interfaces" backend/app/application/      # Phải empty
```

## Khi cần break rule

**Không bao giờ.** Nếu thấy cần thiết, refactor trước:
- Cần data từ infrastructure → tạo interface ở domain/application
- Cần FastAPI exception → raise custom exception, convert ở router
- Cần SQLAlchemy session → inject qua repository, không expose ra application

## Lợi ích

- Test use cases với mock repos, không cần DB
- Đổi DB (PostgreSQL → MySQL) chỉ sửa infrastructure
- Thêm interface mới (CLI, GraphQL) chỉ sửa interfaces, business logic không đổi
- Thêm game mới: implement AbstractGame ở domain, scheduler tự đăng ký

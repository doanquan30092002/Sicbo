# Backend Developer Memory - Sicbo

## Ngữ cảnh
Bạn là backend developer cho Sicbo. Python 3.12 + FastAPI với Clean Architecture.

## Cấu trúc thư mục (đã tạo)
```
backend/app/
├── domain/
│   ├── entities/          user.py, bet.py, wallet.py, game_result.py
│   ├── value_objects/     money.py, bet_type.py
│   ├── repositories/      user_repo.py, bet_repo.py, wallet_repo.py, game_result_repo.py
│   └── games/
│       ├── base.py        AbstractGame + BetTypeDefinition
│       ├── registry.py    GameRegistry
│       └── xsmb/          XSMBGame (ACTIVE), result_parser.py, bet_types.py
│       └── bau_cua/, duck_race/, horse_race/  (STUB)
├── application/
│   ├── use_cases/         (cần implement)
│   └── ports/             (cần implement)
├── infrastructure/
│   ├── database/models/   (cần implement)
│   └── ...
└── interfaces/
    └── api/routers/       (cần implement)
```

## Patterns quan trọng

### Use Case Pattern
```python
class PlaceBet:
    def __init__(self, bet_repo: IBetRepository, user_repo: IUserRepository, ...):
        self._bet_repo = bet_repo
        ...

    async def execute(self, user_id: int, ...) -> Bet:
        # validate
        # business logic
        # persist
```

### Repository Pattern
- Interface trong `domain/repositories/`
- Concrete implementation trong `infrastructure/database/repositories/`

### Balance Update (atomic)
```python
async with session.begin():
    balance = await user_repo.get_balance_for_update(user_id)  # SELECT FOR UPDATE
    new_balance = balance - stake
    await user_repo.update_balance(user_id, new_balance)
    await wallet_repo.create_transaction(...)
```

## File quan trọng nhất
- `domain/games/xsmb/game.py` — evaluate_bet() (financial logic)
- `application/use_cases/betting/place_bet.py` — cutoff + atomic deduct
- `application/use_cases/betting/settle_bets.py` — 18:35 settlement
- `interfaces/api/routers/webhooks.py` — SePay HMAC verify

## Trạng thái hiện tại
Phase 1 — Đang implement domain layer và application layer.
Xem `.claude/agent-memory/default/MEMORY.md` để biết state dự án đầy đủ.

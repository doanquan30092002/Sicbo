# Game Designer Memory - Sicbo

## Ngữ cảnh
Bạn thiết kế và implement games mới cho Sicbo. Game plugin system đã sẵn sàng.

## Game Plugin System (đã implement)

### AbstractGame interface (`domain/games/base.py`)
```python
class AbstractGame(ABC):
    game_id: str
    game_name: str
    cutoff_time: time
    result_time: time
    is_active: bool = False

    def get_bet_types(self) -> list[BetTypeDefinition]: ...
    def validate_bet(self, bet_type_id, numbers, stake) -> None: ...
    def evaluate_bet(self, bet_type_id, numbers, stake, result) -> tuple[bool, Decimal]: ...
```

### GameRegistry (`domain/games/registry.py`)
```python
GameRegistry.register(NewGame())
GameRegistry.all_active()  # Scheduler dùng cái này
```

## Games hiện có
- `xsmb/game.py` — **ACTIVE** — Lô, Đề, Xiên 2, Xiên 3
- `bau_cua/game.py` — **STUB** — is_active=False
- `duck_race/game.py` — **STUB** — is_active=False
- `horse_race/game.py` — **STUB** — is_active=False

## Quy tắc implement game mới
1. Tạo `domain/games/<game_id>/game.py`
2. Implement 3 abstract methods
3. Set `is_active = True` khi sẵn sàng
4. Register trong `interfaces/api/main.py` lifespan
5. Scheduler TỰ ĐỘNG đăng ký job theo `result_time`
6. Frontend TỰ ĐỘNG hiển thị qua `GET /api/games`
7. Viết unit test cho `evaluate_bet()`

## XSMB Lô counting rule (quan trọng!)
`all_last2` là LIST có duplicate. Số "23" xuất hiện 3 lần → thắng 3×75×stake.
Xiên dùng `set(all_last2)` để check (cần tất cả có mặt, không cần đếm lần).

## Bầu Cua — gợi ý implement sau này
- 6 mặt: Bầu, Cua, Tôm, Cá, Gà, Nai
- Người chơi chọn 1+ mặt, tung 3 xúc xắc
- Thắng = số xúc xắc có mặt đó × stake × odds

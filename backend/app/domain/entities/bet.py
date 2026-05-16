from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Bet:
    id: int
    user_id: int
    game_id: str
    draw_date: date
    bet_type_id: str
    numbers: list[str]
    stake_per_point: Decimal
    points: int
    total_stake: Decimal
    potential_win: Decimal
    status: str  # pending | won | lost | cancelled
    win_amount: Decimal
    placed_at: datetime
    source: str  # web | telegram
    settled_at: Optional[datetime] = None

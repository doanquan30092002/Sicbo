from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class GameResult:
    id: int
    game_id: str
    draw_date: date
    parsed_data: dict  # game-specific normalized data
    raw_json: str
    fetched_at: datetime

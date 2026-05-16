from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from typing import Optional

from app.domain.entities.game_result import GameResult


@dataclass
class BetTypeDefinition:
    type_id: str
    display_name: str
    odds: Decimal
    min_numbers: int
    max_numbers: int
    description: str
    number_range: Optional[tuple[int, int]] = None  # (0, 99) hoặc None nếu không dùng số


class AbstractGame(ABC):
    game_id: str
    game_name: str
    cutoff_time: time
    result_time: time
    is_active: bool = False

    @abstractmethod
    def get_bet_types(self) -> list[BetTypeDefinition]:
        """Trả về danh sách bet types của game này."""
        ...

    @abstractmethod
    def validate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal) -> None:
        """Validate input của người chơi. Raise ValueError nếu không hợp lệ."""
        ...

    @abstractmethod
    def evaluate_bet(
        self,
        bet_type_id: str,
        numbers: list[str],
        stake: Decimal,
        result: GameResult,
    ) -> tuple[bool, Decimal]:
        """
        Tính kết quả cược.
        Returns: (won: bool, win_amount: Decimal)
        win_amount = 0 nếu thua.
        """
        ...

    def get_bet_type(self, type_id: str) -> Optional[BetTypeDefinition]:
        for bt in self.get_bet_types():
            if bt.type_id == type_id:
                return bt
        return None

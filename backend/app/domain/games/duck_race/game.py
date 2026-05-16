"""
Đua Vịt - Stub implementation.
is_active = False cho đến khi logic được implement đầy đủ.
"""
from datetime import time
from decimal import Decimal

from app.domain.entities.game_result import GameResult
from app.domain.games.base import AbstractGame, BetTypeDefinition


class DuckRaceGame(AbstractGame):
    game_id = "duck_race"
    game_name = "Đua Vịt"
    cutoff_time = time(19, 0)   # TBD
    result_time = time(19, 30)  # TBD
    is_active = False

    def get_bet_types(self) -> list[BetTypeDefinition]:
        return []

    def validate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal) -> None:
        raise NotImplementedError("Đua Vịt chưa được triển khai.")

    def evaluate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal, result: GameResult) -> tuple[bool, Decimal]:
        raise NotImplementedError("Đua Vịt chưa được triển khai.")

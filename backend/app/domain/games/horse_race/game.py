"""
Đua Ngựa - Stub implementation.
is_active = False cho đến khi logic được implement đầy đủ.
"""
from datetime import time
from decimal import Decimal

from app.domain.entities.game_result import GameResult
from app.domain.games.base import AbstractGame, BetTypeDefinition


class HorseRaceGame(AbstractGame):
    game_id = "horse_race"
    game_name = "Đua Ngựa"
    cutoff_time = time(20, 0)   # TBD
    result_time = time(20, 30)  # TBD
    is_active = False

    def get_bet_types(self) -> list[BetTypeDefinition]:
        return []

    def validate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal) -> None:
        raise NotImplementedError("Đua Ngựa chưa được triển khai.")

    def evaluate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal, result: GameResult) -> tuple[bool, Decimal]:
        raise NotImplementedError("Đua Ngựa chưa được triển khai.")

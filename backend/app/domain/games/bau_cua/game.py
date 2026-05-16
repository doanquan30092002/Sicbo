"""
Bầu Cua Tôm Cá - Stub implementation.
is_active = False cho đến khi logic được implement đầy đủ.
"""
from datetime import time
from decimal import Decimal

from app.domain.entities.game_result import GameResult
from app.domain.games.base import AbstractGame, BetTypeDefinition


class BauCuaGame(AbstractGame):
    game_id = "bau_cua"
    game_name = "Bầu Cua Tôm Cá"
    cutoff_time = time(18, 0)   # TBD
    result_time = time(18, 15)  # TBD
    is_active = False

    def get_bet_types(self) -> list[BetTypeDefinition]:
        return []

    def validate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal) -> None:
        raise NotImplementedError("Bầu Cua chưa được triển khai.")

    def evaluate_bet(self, bet_type_id: str, numbers: list[str], stake: Decimal, result: GameResult) -> tuple[bool, Decimal]:
        raise NotImplementedError("Bầu Cua chưa được triển khai.")

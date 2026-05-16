from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from app.domain.entities.bet import Bet


class IBetRepository(ABC):
    @abstractmethod
    async def create(
        self,
        user_id: int,
        game_id: str,
        draw_date: date,
        bet_type_id: str,
        numbers: list[str],
        stake_per_point: Decimal,
        points: int,
        total_stake: Decimal,
        potential_win: Decimal,
        source: str = "web",
    ) -> Bet: ...

    @abstractmethod
    async def get_by_id(self, bet_id: int) -> Optional[Bet]: ...

    @abstractmethod
    async def get_user_bets(
        self,
        user_id: int,
        game_id: Optional[str] = None,
        draw_date: Optional[date] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Bet], int]: ...

    @abstractmethod
    async def get_pending_bets_for_settlement(self, game_id: str, draw_date: date) -> list[Bet]: ...

    @abstractmethod
    async def update_status(
        self,
        bet_id: int,
        status: str,
        win_amount: Decimal,
    ) -> Bet: ...

    @abstractmethod
    async def cancel(self, bet_id: int) -> Bet: ...

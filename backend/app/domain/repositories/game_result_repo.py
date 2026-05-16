from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from app.domain.entities.game_result import GameResult


class IGameResultRepository(ABC):
    @abstractmethod
    async def create(
        self,
        game_id: str,
        draw_date: date,
        parsed_data: dict,
        raw_json: str,
    ) -> GameResult: ...

    @abstractmethod
    async def get_by_game_and_date(self, game_id: str, draw_date: date) -> Optional[GameResult]: ...

    @abstractmethod
    async def get_recent(self, game_id: str, limit: int = 7) -> list[GameResult]: ...

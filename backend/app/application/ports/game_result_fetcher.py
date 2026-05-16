from abc import ABC, abstractmethod
from datetime import date


class IGameResultFetcher(ABC):
    @abstractmethod
    async def fetch(self, game_id: str, draw_date: date) -> dict:
        """
        Lấy raw result từ external API cho game và ngày cụ thể.
        Returns raw dict (sẽ được parse bởi game's result_parser).
        Raises Exception nếu không lấy được kết quả.
        """
        ...

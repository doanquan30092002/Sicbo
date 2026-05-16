import logging
from datetime import date

from app.application.ports.game_result_fetcher import IGameResultFetcher
from app.domain.entities.game_result import GameResult
from app.domain.games.registry import GameRegistry
from app.domain.games.xsmb.result_parser import parse_xsmb_result
from app.domain.repositories.game_result_repo import IGameResultRepository

logger = logging.getLogger(__name__)

PARSERS = {
    "xsmb": parse_xsmb_result,
}


class FetchAndStoreResult:
    def __init__(
        self,
        game_result_repo: IGameResultRepository,
        result_fetcher: IGameResultFetcher,
    ):
        self._game_result_repo = game_result_repo
        self._result_fetcher = result_fetcher

    async def execute(self, game_id: str, draw_date: date) -> GameResult:
        existing = await self._game_result_repo.get_by_game_and_date(game_id, draw_date)
        if existing:
            logger.info(f"Kết quả {game_id}/{draw_date} đã tồn tại, bỏ qua fetch.")
            return existing

        raw = await self._result_fetcher.fetch(game_id, draw_date)

        parser = PARSERS.get(game_id)
        if not parser:
            raise ValueError(f"Không có parser cho game '{game_id}'.")

        parsed_data = parser(raw)

        import json
        result = await self._game_result_repo.create(
            game_id=game_id,
            draw_date=draw_date,
            parsed_data=parsed_data,
            raw_json=json.dumps(raw, ensure_ascii=False),
        )

        logger.info(f"Đã lưu kết quả {game_id}/{draw_date}: ĐB={parsed_data.get('special_prize')}")
        return result

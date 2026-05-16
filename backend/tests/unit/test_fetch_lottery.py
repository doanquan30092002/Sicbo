"""Unit tests cho FetchAndStoreResult use case."""
from datetime import date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.lottery.fetch_and_store_result import FetchAndStoreResult
from app.domain.entities.game_result import GameResult


SAMPLE_RAW = {
    "db": "12345",
    "g1": "23456",
    "g2": ["11122"],
    "g3": [], "g4": [], "g5": [], "g6": [], "g7": [],
}


class TestFetchAndStoreResult:
    async def test_fetches_and_stores_new_result(self):
        repo = AsyncMock()
        fetcher = AsyncMock()
        repo.get_by_game_and_date.return_value = None
        fetcher.fetch.return_value = SAMPLE_RAW
        repo.create.return_value = GameResult(
            id=1, game_id="xsmb", draw_date=date.today(),
            parsed_data={}, raw_json="{}", fetched_at=datetime.now(),
        )

        uc = FetchAndStoreResult(repo, fetcher)
        await uc.execute("xsmb", date.today())

        fetcher.fetch.assert_awaited_once_with("xsmb", date.today())
        repo.create.assert_awaited_once()
        parsed = repo.create.await_args.kwargs["parsed_data"]
        assert parsed["special_last2"] == "45"
        assert isinstance(parsed["all_last2"], list)

    async def test_idempotent_when_already_exists(self):
        repo = AsyncMock()
        fetcher = AsyncMock()
        existing = GameResult(id=1, game_id="xsmb", draw_date=date.today(),
                              parsed_data={}, raw_json="{}", fetched_at=datetime.now())
        repo.get_by_game_and_date.return_value = existing

        uc = FetchAndStoreResult(repo, fetcher)
        out = await uc.execute("xsmb", date.today())

        assert out is existing
        fetcher.fetch.assert_not_called()
        repo.create.assert_not_called()

    async def test_unknown_game_raises(self):
        repo = AsyncMock()
        fetcher = AsyncMock()
        repo.get_by_game_and_date.return_value = None
        fetcher.fetch.return_value = SAMPLE_RAW

        uc = FetchAndStoreResult(repo, fetcher)
        with pytest.raises(ValueError, match="parser"):
            await uc.execute("unknown_game", date.today())

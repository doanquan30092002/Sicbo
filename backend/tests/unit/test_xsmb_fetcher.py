"""Unit tests cho XSMBFetcher — mock httpx."""
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.domain.games.xsmb.result_parser import parse_xsmb_result
from app.infrastructure.external.xsmb_fetcher import XSMBFetcher


SAMPLE_ENTRY = {
    "id": 4203,
    "date": "16/05/2026",
    "region": "MB",
    "data": {
        "DB": "19404",
        "G1": "88678",
        "G2": ["39224", "96731"],
        "G3": ["84491", "73570", "57612", "69204", "74927", "10074"],
        "G4": ["8566", "4186", "2260", "3987"],
        "G5": ["9080", "1968", "2864", "2838", "8548", "6997"],
        "G6": ["948", "185", "007"],
        "G7": ["66", "60", "81", "84"],
    },
}


def _mock_response(payload, status_code=200):
    r = MagicMock(spec=httpx.Response)
    r.status_code = status_code
    r.raise_for_status = MagicMock()
    r.json = MagicMock(return_value=payload)
    return r


class TestXSMBFetcher:
    async def test_rejects_non_xsmb_game(self):
        fetcher = XSMBFetcher()
        with pytest.raises(ValueError, match="xsmb"):
            await fetcher.fetch("bau_cua", date(2026, 5, 16))

    async def test_fetch_returns_data_from_latest(self):
        fetcher = XSMBFetcher()
        with patch("httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            instance.get = AsyncMock(return_value=_mock_response([SAMPLE_ENTRY]))

            raw = await fetcher.fetch("xsmb", date(2026, 5, 16))
            assert raw["DB"] == "19404"
            assert raw["G7"] == ["66", "60", "81", "84"]

    async def test_fetch_fallback_to_history_when_latest_misses_date(self):
        fetcher = XSMBFetcher()
        old_entry = {**SAMPLE_ENTRY, "date": "15/05/2026"}

        with patch("httpx.AsyncClient") as MockClient:
            instance = MockClient.return_value.__aenter__.return_value
            # latest trả về entry của ngày khác → fallback history
            instance.get = AsyncMock(side_effect=[
                _mock_response([old_entry]),       # latest call
                _mock_response([SAMPLE_ENTRY]),    # history call
            ])

            raw = await fetcher.fetch("xsmb", date(2026, 5, 16))
            assert raw["DB"] == "19404"
            assert instance.get.await_count == 2

    async def test_parsed_result_has_expected_shape(self):
        parsed = parse_xsmb_result(SAMPLE_ENTRY)
        assert parsed["special_prize"] == "19404"
        assert parsed["special_last2"] == "04"
        assert isinstance(parsed["all_last2"], list)
        # Đếm "04": xuất hiện trong DB (19404) + G3 (69204) → 2 lần
        assert parsed["all_last2"].count("04") == 2
        # "66" xuất hiện ở G7
        assert "66" in parsed["all_last2"]
        # "60" xuất hiện ở G7 (60) + G4 (2260) → 2 lần
        assert parsed["all_last2"].count("60") == 2

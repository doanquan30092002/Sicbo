"""XSMB result fetcher — xosonhanh.vn API.

Endpoints:
- GET /wp-json/xosonhanh/v1/latest/MB         → array 10 kết quả gần nhất
- GET /wp-json/xosonhanh/v1/history?date=DD/MM/YYYY  → kết quả 1 ngày

Rate limit: 500 req/day/IP, no auth.
"""
import logging
from datetime import date

import httpx

from app.application.ports.game_result_fetcher import IGameResultFetcher
from app.config import settings

logger = logging.getLogger(__name__)


class XSMBFetcher(IGameResultFetcher):
    """Fetcher cho game_id='xsmb' qua xosonhanh.vn."""

    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    async def fetch(self, game_id: str, draw_date: date) -> dict:
        if game_id != "xsmb":
            raise ValueError(f"XSMBFetcher chỉ hỗ trợ game_id='xsmb', nhận: {game_id}")

        # Format DD/MM/YYYY theo spec API
        date_str = draw_date.strftime("%d/%m/%Y")

        # Strategy 1: thử latest endpoint trước (rẻ hơn, trả 10 results)
        try:
            latest = await self._fetch_latest()
            for entry in latest:
                if entry.get("date") == date_str:
                    return self._extract_data(entry)
        except Exception as e:
            logger.warning(f"latest/MB fetch fail ({e}), fallback history endpoint.")

        # Strategy 2: history theo ngày
        return await self._fetch_history(date_str)

    async def _fetch_latest(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(settings.xsmb_api_latest)
            r.raise_for_status()
            payload = r.json()
        if not isinstance(payload, list):
            raise ValueError(f"latest/MB response không phải array: {type(payload)}")
        return payload

    async def _fetch_history(self, date_str: str) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(settings.xsmb_api_history, params={"date": date_str})
            r.raise_for_status()
            payload = r.json()

        # history có thể trả list hoặc object
        if isinstance(payload, list):
            if not payload:
                raise RuntimeError(f"Không có kết quả XSMB cho ngày {date_str}.")
            entry = payload[0]
        elif isinstance(payload, dict):
            entry = payload
        else:
            raise ValueError(f"history response không hợp lệ: {type(payload)}")

        return self._extract_data(entry)

    @staticmethod
    def _extract_data(entry: dict) -> dict:
        """Trả về raw dict đã unwrap khỏi 'data' để parser xử lý."""
        if "data" in entry and isinstance(entry["data"], dict):
            return entry["data"]
        return entry

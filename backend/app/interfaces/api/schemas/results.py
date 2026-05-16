"""Pydantic schemas cho lottery results endpoint."""
from datetime import date, datetime

from pydantic import BaseModel


class GameResultResponse(BaseModel):
    id: int
    game_id: str
    draw_date: date
    parsed_data: dict
    fetched_at: datetime


class GameResultListResponse(BaseModel):
    items: list[GameResultResponse]

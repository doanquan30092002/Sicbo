"""Pydantic schemas cho betting endpoints."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PlaceBetRequest(BaseModel):
    game_id: str
    bet_type_id: str
    numbers: list[str] = Field(min_length=1, max_length=10)
    stake_per_point: Decimal = Field(gt=0)
    points: int = Field(default=1, ge=1, le=100)


class BetResponse(BaseModel):
    id: int
    user_id: int
    game_id: str
    draw_date: date
    bet_type_id: str
    numbers: list[str]
    stake_per_point: Decimal
    points: int
    total_stake: Decimal
    potential_win: Decimal
    status: str
    win_amount: Decimal
    source: str
    placed_at: datetime
    settled_at: Optional[datetime] = None


class BetListResponse(BaseModel):
    items: list[BetResponse]
    total: int
    page: int
    limit: int


class BetTypeOut(BaseModel):
    type_id: str
    display_name: str
    odds: Decimal
    min_numbers: int
    max_numbers: int
    description: str


class GameOut(BaseModel):
    game_id: str
    game_name: str
    cutoff_time: str  # "HH:MM"
    result_time: str
    is_active: bool
    bet_types: list[BetTypeOut]


class CutoffStatusOut(BaseModel):
    game_id: str
    is_open: bool
    cutoff_time: str
    server_time: str
    seconds_until_cutoff: int

"""Lottery results router — kết quả XSMB hôm nay / theo ngày / lịch sử."""
from datetime import date as date_type
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.infrastructure.database.repositories.game_result_repository import (
    GameResultRepository,
)
from app.interfaces.api.dependencies import get_game_result_repo
from app.interfaces.api.schemas.results import GameResultListResponse, GameResultResponse

router = APIRouter(prefix="/api/results", tags=["results"])

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


@router.get("/{game_id}/today", response_model=GameResultResponse)
async def get_today(
    game_id: str,
    repo: GameResultRepository = Depends(get_game_result_repo),
):
    today = datetime.now(VN_TZ).date()
    result = await repo.get_by_game_and_date(game_id, today)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chưa có kết quả {game_id} cho hôm nay.",
        )
    return GameResultResponse.model_validate(result, from_attributes=True)


@router.get("/{game_id}/{draw_date}", response_model=GameResultResponse)
async def get_by_date(
    game_id: str,
    draw_date: date_type,
    repo: GameResultRepository = Depends(get_game_result_repo),
):
    result = await repo.get_by_game_and_date(game_id, draw_date)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không có kết quả {game_id} ngày {draw_date}.",
        )
    return GameResultResponse.model_validate(result, from_attributes=True)


@router.get("/{game_id}", response_model=GameResultListResponse)
async def get_recent(
    game_id: str,
    limit: int = Query(default=7, ge=1, le=30),
    repo: GameResultRepository = Depends(get_game_result_repo),
):
    items = await repo.get_recent(game_id, limit=limit)
    return GameResultListResponse(
        items=[GameResultResponse.model_validate(r, from_attributes=True) for r in items]
    )

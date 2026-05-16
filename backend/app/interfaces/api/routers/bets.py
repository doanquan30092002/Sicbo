"""Bets router — POST/GET/DELETE bets."""
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.use_cases.betting.cancel_bet import BetNotCancellableError, CancelBet
from app.application.use_cases.betting.place_bet import (
    CutoffPassedError,
    InsufficientBalanceError,
    PlaceBet,
)
from app.domain.entities.user import User
from app.infrastructure.database.repositories.bet_repository import BetRepository
from app.interfaces.api.dependencies import (
    get_bet_repo,
    get_cancel_bet_uc,
    get_current_user,
    get_place_bet_uc,
)
from app.interfaces.api.schemas.bets import BetListResponse, BetResponse, PlaceBetRequest

router = APIRouter(prefix="/api/bets", tags=["bets"])


@router.post("", response_model=BetResponse, status_code=status.HTTP_201_CREATED)
async def place_bet(
    body: PlaceBetRequest,
    user: User = Depends(get_current_user),
    uc: PlaceBet = Depends(get_place_bet_uc),
):
    try:
        bet = await uc.execute(
            user_id=user.id,
            game_id=body.game_id,
            bet_type_id=body.bet_type_id,
            numbers=body.numbers,
            stake_per_point=body.stake_per_point,
            points=body.points,
            source="web",
        )
    except CutoffPassedError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return BetResponse.model_validate(bet, from_attributes=True)


@router.get("", response_model=BetListResponse)
async def list_my_bets(
    user: User = Depends(get_current_user),
    bet_repo: BetRepository = Depends(get_bet_repo),
    game_id: Optional[str] = Query(default=None),
    draw_date: Optional[date_type] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    bets, total = await bet_repo.get_user_bets(
        user_id=user.id,
        game_id=game_id,
        draw_date=draw_date,
        status=status_filter,
        page=page,
        limit=limit,
    )
    return BetListResponse(
        items=[BetResponse.model_validate(b, from_attributes=True) for b in bets],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{bet_id}", response_model=BetResponse)
async def get_bet(
    bet_id: int,
    user: User = Depends(get_current_user),
    bet_repo: BetRepository = Depends(get_bet_repo),
):
    bet = await bet_repo.get_by_id(bet_id)
    if not bet or bet.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lệnh cược không tồn tại.")
    return BetResponse.model_validate(bet, from_attributes=True)


@router.delete("/{bet_id}", response_model=BetResponse)
async def cancel_bet(
    bet_id: int,
    user: User = Depends(get_current_user),
    uc: CancelBet = Depends(get_cancel_bet_uc),
):
    try:
        bet = await uc.execute(user_id=user.id, bet_id=bet_id)
    except BetNotCancellableError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return BetResponse.model_validate(bet, from_attributes=True)

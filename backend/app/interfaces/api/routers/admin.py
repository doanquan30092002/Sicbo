"""Admin router — duyệt rút tiền, quản lý user, stats. Yêu cầu is_admin=True."""
import logging
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.application.use_cases.admin.process_withdrawal import ProcessWithdrawal
from app.domain.entities.user import User
from app.infrastructure.database.models.bet_model import BetModel
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.interfaces.api.dependencies import (
    get_current_admin,
    get_process_withdrawal_uc,
    get_session,
    get_user_repo,
    get_wallet_repo,
)
from app.interfaces.api.schemas.auth import UserResponse
from app.interfaces.api.schemas.wallet import (
    AdminStatsResponse,
    AdminWithdrawalActionRequest,
    WithdrawalListResponse,
    WithdrawalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


# ---------- Withdrawals ----------

@router.get("/withdrawals/pending", response_model=WithdrawalListResponse)
async def list_pending_withdrawals(
    _admin: User = Depends(get_current_admin),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    items, total = await wallet_repo.get_pending_withdrawals(page=page, limit=limit)
    return WithdrawalListResponse(
        items=[WithdrawalResponse.model_validate(w, from_attributes=True) for w in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("/withdrawals/{withdrawal_id}/approve", response_model=WithdrawalResponse)
async def approve_withdrawal(
    withdrawal_id: int,
    admin: User = Depends(get_current_admin),
    uc: ProcessWithdrawal = Depends(get_process_withdrawal_uc),
):
    try:
        w = await uc.approve(withdrawal_id, admin.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return WithdrawalResponse.model_validate(w, from_attributes=True)


@router.post("/withdrawals/{withdrawal_id}/reject", response_model=WithdrawalResponse)
async def reject_withdrawal(
    withdrawal_id: int,
    body: AdminWithdrawalActionRequest,
    admin: User = Depends(get_current_admin),
    uc: ProcessWithdrawal = Depends(get_process_withdrawal_uc),
):
    try:
        w = await uc.reject(withdrawal_id, admin.id, reason=body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return WithdrawalResponse.model_validate(w, from_attributes=True)


# ---------- Users ----------

@router.get("/users")
async def list_users(
    _admin: User = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repo),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    users, total = await user_repo.list_users(page=page, limit=limit, search=search)
    return {
        "items": [UserResponse.model_validate(u, from_attributes=True) for u in users],
        "total": total,
        "page": page,
        "limit": limit,
    }


# ---------- Stats ----------

@router.get("/stats", response_model=AdminStatsResponse)
async def stats(
    _admin: User = Depends(get_current_admin),
    session=Depends(get_session),
):
    today = datetime.now(VN_TZ).date()

    total_users = (
        await session.execute(select(func.count(UserModel.id)))
    ).scalar_one()

    from app.domain.value_objects.bet_type import WithdrawalStatus
    from app.infrastructure.database.models.transaction_model import WithdrawalModel

    pending_w = (
        await session.execute(
            select(func.count(WithdrawalModel.id)).where(
                WithdrawalModel.status == WithdrawalStatus.PENDING.value
            )
        )
    ).scalar_one()

    today_bets_count = (
        await session.execute(
            select(func.count(BetModel.id)).where(BetModel.draw_date == today)
        )
    ).scalar_one()

    today_total_stake = (
        await session.execute(
            select(func.coalesce(func.sum(BetModel.total_stake), 0)).where(
                BetModel.draw_date == today
            )
        )
    ).scalar_one()

    today_total_payout = (
        await session.execute(
            select(func.coalesce(func.sum(BetModel.win_amount), 0)).where(
                BetModel.draw_date == today
            )
        )
    ).scalar_one()

    return AdminStatsResponse(
        total_users=total_users,
        total_pending_withdrawals=pending_w,
        today_bets=today_bets_count,
        today_total_stake=today_total_stake,
        today_total_payout=today_total_payout,
    )

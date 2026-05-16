"""Wallet router — deposit, withdrawal, transactions cho user."""
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.use_cases.wallet.request_deposit import RequestDeposit
from app.application.use_cases.wallet.request_withdrawal import (
    InsufficientBalanceError,
    RequestWithdrawal,
)
from app.config import settings
from app.domain.entities.user import User
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.interfaces.api.dependencies import (
    get_current_user,
    get_request_deposit_uc,
    get_request_withdrawal_uc,
    get_wallet_repo,
)
from app.interfaces.api.schemas.wallet import (
    DepositInitRequest,
    DepositInitResponse,
    TransactionListResponse,
    TransactionResponse,
    WithdrawalRequest,
    WithdrawalResponse,
)

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


def _build_sepay_qr_url(
    amount: int,
    transfer_content: str,
    bank_name: str,
    account_no: str,
) -> str:
    """Tạo URL ảnh QR VietQR qua sepay.vn (miễn phí)."""
    base = "https://qr.sepay.vn/img"
    params = {
        "bank": bank_name,
        "acc": account_no,
        "template": "compact",
        "amount": str(amount),
        "des": transfer_content,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


# ---------- Deposit ----------

@router.post(
    "/deposit/init",
    response_model=DepositInitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def init_deposit(
    body: DepositInitRequest,
    user: User = Depends(get_current_user),
    uc: RequestDeposit = Depends(get_request_deposit_uc),
):
    try:
        deposit = await uc.execute(
            user_id=user.id,
            amount=body.amount,
            payment_method=body.payment_method,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    qr_url = None
    if body.payment_method == "bank_transfer" and settings.bank_account_no:
        qr_url = _build_sepay_qr_url(
            amount=int(deposit.amount),
            transfer_content=deposit.transfer_content,
            bank_name=settings.bank_name,
            account_no=settings.bank_account_no,
        )

    return DepositInitResponse(
        deposit_id=deposit.id,
        amount=deposit.amount,
        payment_method=deposit.payment_method,
        transfer_content=deposit.transfer_content,
        bank_account=deposit.bank_account,
        bank_name=settings.bank_name if body.payment_method == "bank_transfer" else None,
        bank_account_name=settings.bank_account_name if body.payment_method == "bank_transfer" else None,
        qr_url=qr_url,
        status=deposit.status,
        created_at=deposit.created_at,
    )


@router.get("/deposits/{deposit_id}", response_model=DepositInitResponse)
async def get_deposit(
    deposit_id: int,
    user: User = Depends(get_current_user),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
):
    deposit = await wallet_repo.get_deposit_by_id(deposit_id)
    if not deposit or deposit.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lệnh nạp không tồn tại.",
        )

    qr_url = None
    if deposit.payment_method == "bank_transfer" and settings.bank_account_no:
        qr_url = _build_sepay_qr_url(
            amount=int(deposit.amount),
            transfer_content=deposit.transfer_content,
            bank_name=settings.bank_name,
            account_no=settings.bank_account_no,
        )

    return DepositInitResponse(
        deposit_id=deposit.id,
        amount=deposit.amount,
        payment_method=deposit.payment_method,
        transfer_content=deposit.transfer_content,
        bank_account=deposit.bank_account,
        bank_name=settings.bank_name if deposit.payment_method == "bank_transfer" else None,
        bank_account_name=settings.bank_account_name if deposit.payment_method == "bank_transfer" else None,
        qr_url=qr_url,
        status=deposit.status,
        created_at=deposit.created_at,
    )


# ---------- Withdrawal ----------

@router.post(
    "/withdraw",
    response_model=WithdrawalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_withdrawal(
    body: WithdrawalRequest,
    user: User = Depends(get_current_user),
    uc: RequestWithdrawal = Depends(get_request_withdrawal_uc),
):
    try:
        withdrawal = await uc.execute(
            user_id=user.id,
            amount=body.amount,
            payment_method=body.payment_method,
            account_number=body.account_number,
            account_name=body.account_name,
            bank_name=body.bank_name,
        )
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return WithdrawalResponse.model_validate(withdrawal, from_attributes=True)


# ---------- Transactions / Balance ----------

@router.get("/balance")
async def get_balance(user: User = Depends(get_current_user)):
    return {"user_id": user.id, "balance": user.balance}


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    user: User = Depends(get_current_user),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    txs, total = await wallet_repo.get_transactions(user.id, page=page, limit=limit)
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t, from_attributes=True) for t in txs],
        total=total,
        page=page,
        limit=limit,
    )

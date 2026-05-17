"""Pydantic schemas cho wallet endpoints (deposit, withdrawal, transactions)."""
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- Deposit ----------

class DepositInitRequest(BaseModel):
    amount: Decimal = Field(gt=0, description="Số tiền nạp (VND), bội số của 1,000")
    payment_method: Literal["bank_transfer", "momo"] = "bank_transfer"


class DepositInitResponse(BaseModel):
    deposit_id: int
    amount: Decimal
    payment_method: str
    transfer_content: str
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    qr_url: Optional[str] = None
    status: str
    created_at: datetime


class DepositResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    payment_method: str
    transfer_content: str
    status: str
    bank_account: Optional[str] = None
    sepay_transaction_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime


# ---------- Withdrawal ----------

class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(ge=50000, description="Số tiền rút (VND), tối thiểu 50,000")
    payment_method: Literal["bank_transfer", "momo"] = "bank_transfer"
    account_number: str = Field(min_length=6, max_length=30)
    account_name: str = Field(min_length=2, max_length=100)
    bank_name: Optional[str] = Field(default=None, max_length=100)


class WithdrawalResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    payment_method: str
    account_number: str
    account_name: str
    bank_name: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    requested_at: datetime


class WithdrawalListResponse(BaseModel):
    items: list[WithdrawalResponse]
    total: int
    page: int
    limit: int


# ---------- Transaction ----------

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str
    reference_id: Optional[str] = None
    description: Optional[str] = None
    related_bet_id: Optional[int] = None
    created_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    limit: int


# ---------- SePay webhook ----------

class SePayWebhookPayload(BaseModel):
    """Subset of SePay webhook payload. SePay gửi rất nhiều field, chỉ cần các field này."""

    id: Optional[int] = None  # SePay internal id
    gateway: Optional[str] = None
    transactionDate: Optional[str] = None
    accountNumber: Optional[str] = None
    content: str = Field(description="Nội dung chuyển khoản (chứa NAPxxxxxx)")
    transferType: str = Field(description="in | out")
    transferAmount: Decimal = Field(description="Số tiền")
    referenceCode: Optional[str] = None
    description: Optional[str] = None


# ---------- Admin ----------

class AdminWithdrawalActionRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=500)


class DepositListResponse(BaseModel):
    items: list[DepositResponse]
    total: int
    page: int
    limit: int


class AdminConfirmDepositRequest(BaseModel):
    override_amount: Optional[Decimal] = Field(default=None, gt=0, description="Số tiền thực tế nhận (mặc định = deposit.amount)")
    note: Optional[str] = Field(default=None, max_length=500)


class AdminCreditDirectRequest(BaseModel):
    user_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)
    note: Optional[str] = Field(default=None, max_length=500)


class AdminStatsResponse(BaseModel):
    total_users: int
    total_pending_withdrawals: int
    today_bets: int
    today_total_stake: Decimal
    today_total_payout: Decimal

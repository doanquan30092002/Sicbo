from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_bet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bets.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DepositModel(Base):
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    transfer_content: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sepay_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WithdrawalModel(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

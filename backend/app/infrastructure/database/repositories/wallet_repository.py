"""Concrete WalletRepository — PostgreSQL via SQLAlchemy async."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.wallet import Deposit, Transaction, Withdrawal
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import DepositStatus, WithdrawalStatus
from app.infrastructure.database.models.transaction_model import (
    DepositModel,
    TransactionModel,
    WithdrawalModel,
)


def _to_tx(m: TransactionModel) -> Transaction:
    return Transaction(
        id=m.id,
        user_id=m.user_id,
        type=m.type,
        amount=m.amount,
        balance_before=m.balance_before,
        balance_after=m.balance_after,
        status=m.status,
        created_at=m.created_at,
        reference_id=m.reference_id,
        description=m.description,
        related_bet_id=m.related_bet_id,
    )


def _to_deposit(m: DepositModel) -> Deposit:
    return Deposit(
        id=m.id,
        user_id=m.user_id,
        amount=m.amount,
        payment_method=m.payment_method,
        transfer_content=m.transfer_content,
        status=m.status,
        created_at=m.created_at,
        bank_account=m.bank_account,
        sepay_transaction_id=m.sepay_transaction_id,
        confirmed_at=m.confirmed_at,
    )


def _to_withdrawal(m: WithdrawalModel) -> Withdrawal:
    return Withdrawal(
        id=m.id,
        user_id=m.user_id,
        amount=m.amount,
        payment_method=m.payment_method,
        account_number=m.account_number,
        account_name=m.account_name,
        status=m.status,
        requested_at=m.requested_at,
        bank_name=m.bank_name,
        admin_note=m.admin_note,
        processed_by=m.processed_by,
        processed_at=m.processed_at,
    )


class WalletRepository(IWalletRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_transaction(
        self,
        user_id: int,
        type: str,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        status: str = "completed",
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
        related_bet_id: Optional[int] = None,
    ) -> Transaction:
        m = TransactionModel(
            user_id=user_id,
            type=type.value if hasattr(type, "value") else type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            status=status,
            reference_id=reference_id,
            description=description,
            related_bet_id=related_bet_id,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_tx(m)

    async def get_transactions(
        self, user_id: int, page: int = 1, limit: int = 20
    ) -> tuple[list[Transaction], int]:
        count_stmt = select(func.count(TransactionModel.id)).where(
            TransactionModel.user_id == user_id
        )
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(TransactionModel)
            .where(TransactionModel.user_id == user_id)
            .order_by(TransactionModel.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_tx(m) for m in rows], total

    async def create_deposit(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        transfer_content: str,
        bank_account: Optional[str] = None,
    ) -> Deposit:
        m = DepositModel(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            transfer_content=transfer_content,
            bank_account=bank_account,
            status=DepositStatus.PENDING.value,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_deposit(m)

    async def get_deposit_by_transfer_content(
        self, transfer_content: str
    ) -> Optional[Deposit]:
        stmt = select(DepositModel).where(DepositModel.transfer_content == transfer_content)
        m = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_deposit(m) if m else None

    async def get_deposit_by_id(self, deposit_id: int) -> Optional[Deposit]:
        m = await self._session.get(DepositModel, deposit_id)
        return _to_deposit(m) if m else None

    async def confirm_deposit(self, deposit_id: int, sepay_transaction_id: str) -> Deposit:
        m = await self._session.get(DepositModel, deposit_id)
        if m is None:
            raise ValueError(f"Deposit #{deposit_id} không tồn tại.")
        m.status = DepositStatus.CONFIRMED.value
        m.sepay_transaction_id = sepay_transaction_id
        m.confirmed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _to_deposit(m)

    async def get_pending_deposits(
        self, page: int = 1, limit: int = 20
    ) -> tuple[list[Deposit], int]:
        count_stmt = select(func.count(DepositModel.id)).where(
            DepositModel.status == DepositStatus.PENDING.value
        )
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            select(DepositModel)
            .where(DepositModel.status == DepositStatus.PENDING.value)
            .order_by(DepositModel.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_deposit(m) for m in rows], total

    async def create_withdrawal(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        account_number: str,
        account_name: str,
        bank_name: Optional[str] = None,
    ) -> Withdrawal:
        m = WithdrawalModel(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            account_number=account_number,
            account_name=account_name,
            bank_name=bank_name,
            status=WithdrawalStatus.PENDING.value,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_withdrawal(m)

    async def get_pending_withdrawals(
        self, page: int = 1, limit: int = 20
    ) -> tuple[list[Withdrawal], int]:
        count_stmt = select(func.count(WithdrawalModel.id)).where(
            WithdrawalModel.status == WithdrawalStatus.PENDING.value
        )
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            select(WithdrawalModel)
            .where(WithdrawalModel.status == WithdrawalStatus.PENDING.value)
            .order_by(WithdrawalModel.requested_at.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_withdrawal(m) for m in rows], total

    async def update_withdrawal_status(
        self,
        withdrawal_id: int,
        status: str,
        admin_note: Optional[str] = None,
        processed_by: Optional[int] = None,
    ) -> Withdrawal:
        m = await self._session.get(WithdrawalModel, withdrawal_id)
        if m is None:
            raise ValueError(f"Withdrawal #{withdrawal_id} không tồn tại.")
        m.status = status.value if hasattr(status, "value") else status
        if admin_note is not None:
            m.admin_note = admin_note
        if processed_by is not None:
            m.processed_by = processed_by
        m.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return _to_withdrawal(m)

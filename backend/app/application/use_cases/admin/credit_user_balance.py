"""Admin use case: nạp tiền thủ công cho user (bootstrap khi chưa có cổng thanh toán tự động).

Hai kịch bản:
1. Xác nhận deposit pending có sẵn (user đã tạo lệnh nạp): `confirm_pending_deposit(deposit_id, admin_id)`
2. Cộng tiền trực tiếp (không qua deposit): `credit_direct(user_id, amount, note, admin_id)`
"""
import logging
from decimal import Decimal
from typing import Optional

from app.application.ports.notification_port import INotificationPort
from app.domain.entities.wallet import Deposit, Transaction
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import DepositStatus, TransactionType

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class DepositNotFoundError(Exception):
    pass


class DepositAlreadyProcessedError(Exception):
    pass


class CreditUserBalance:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        user_repo: IUserRepository,
        notification_port: INotificationPort,
    ):
        self._wallet_repo = wallet_repo
        self._user_repo = user_repo
        self._notification = notification_port

    async def confirm_pending_deposit(
        self,
        deposit_id: int,
        admin_id: int,
        override_amount: Optional[Decimal] = None,
        note: Optional[str] = None,
    ) -> Deposit:
        deposit = await self._wallet_repo.get_deposit_by_id(deposit_id)
        if deposit is None:
            raise DepositNotFoundError(f"Deposit #{deposit_id} không tồn tại.")
        if deposit.status != DepositStatus.PENDING.value:
            raise DepositAlreadyProcessedError(
                f"Deposit #{deposit_id} đã ở trạng thái '{deposit.status}', không thể confirm lại."
            )

        credit_amount = override_amount if override_amount is not None else deposit.amount

        balance = await self._user_repo.get_balance_for_update(deposit.user_id)
        new_balance = balance + credit_amount

        await self._user_repo.update_balance(deposit.user_id, new_balance)
        ref = f"admin_manual_{admin_id}_d{deposit.id}"
        confirmed = await self._wallet_repo.confirm_deposit(deposit.id, ref)
        await self._wallet_repo.create_transaction(
            user_id=deposit.user_id,
            type=TransactionType.DEPOSIT,
            amount=credit_amount,
            balance_before=balance,
            balance_after=new_balance,
            reference_id=ref,
            description=note or f"Admin #{admin_id} xác nhận nạp thủ công",
        )

        user = await self._user_repo.get_by_id(deposit.user_id)
        if user and user.telegram_id:
            await self._notification.send_user_message(
                user.telegram_id,
                f"✅ Nạp tiền đã được admin xác nhận!\n"
                f"💵 +{credit_amount:,.0f} VND\n"
                f"💰 Số dư: {new_balance:,.0f} VND",
            )

        logger.info(
            f"Admin #{admin_id} confirmed deposit #{deposit.id} for user {deposit.user_id}: +{credit_amount}"
        )
        return confirmed

    async def credit_direct(
        self,
        user_id: int,
        amount: Decimal,
        admin_id: int,
        note: Optional[str] = None,
    ) -> Transaction:
        if amount <= 0:
            raise ValueError("Số tiền phải > 0.")

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User #{user_id} không tồn tại.")

        balance = await self._user_repo.get_balance_for_update(user_id)
        new_balance = balance + amount

        await self._user_repo.update_balance(user_id, new_balance)
        tx = await self._wallet_repo.create_transaction(
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            amount=amount,
            balance_before=balance,
            balance_after=new_balance,
            reference_id=f"admin_credit_{admin_id}",
            description=note or f"Admin #{admin_id} cộng tiền thủ công",
        )

        if user.telegram_id:
            await self._notification.send_user_message(
                user.telegram_id,
                f"💰 Admin đã cộng tiền vào tài khoản!\n"
                f"💵 +{amount:,.0f} VND\n"
                f"💰 Số dư mới: {new_balance:,.0f} VND" + (f"\n📝 Ghi chú: {note}" if note else ""),
            )

        logger.info(f"Admin #{admin_id} credited user {user_id}: +{amount} (new balance: {new_balance})")
        return tx

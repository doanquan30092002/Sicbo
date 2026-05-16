import logging
from decimal import Decimal
from typing import Optional

from app.application.ports.notification_port import INotificationPort
from app.domain.entities.wallet import Withdrawal
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import TransactionType

logger = logging.getLogger(__name__)

MIN_WITHDRAWAL = Decimal("50000")  # 50,000 VND


class InsufficientBalanceError(Exception):
    pass


class RequestWithdrawal:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        user_repo: IUserRepository,
        notification_port: INotificationPort,
    ):
        self._wallet_repo = wallet_repo
        self._user_repo = user_repo
        self._notification = notification_port

    async def execute(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        account_number: str,
        account_name: str,
        bank_name: Optional[str] = None,
    ) -> Withdrawal:
        if amount < MIN_WITHDRAWAL:
            raise ValueError(f"Số tiền rút tối thiểu là {MIN_WITHDRAWAL:,.0f} VND.")
        if amount % 1000 != 0:
            raise ValueError("Số tiền rút phải là bội số của 1,000 VND.")

        # Deduct balance immediately (refund nếu admin reject)
        balance = await self._user_repo.get_balance_for_update(user_id)
        if balance < amount:
            raise InsufficientBalanceError(
                f"Số dư không đủ. Cần {amount:,.0f} VND, hiện có {balance:,.0f} VND."
            )

        new_balance = balance - amount
        await self._user_repo.update_balance(user_id, new_balance)

        withdrawal = await self._wallet_repo.create_withdrawal(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            account_number=account_number,
            account_name=account_name,
            bank_name=bank_name,
        )

        await self._wallet_repo.create_transaction(
            user_id=user_id,
            type=TransactionType.WITHDRAW,
            amount=amount,
            balance_before=balance,
            balance_after=new_balance,
            status="pending",
            description=f"Yêu cầu rút tiền #{withdrawal.id}",
        )

        # Notify admin
        await self._notification.send_admin_message(
            f"💸 *YÊU CẦU RÚT TIỀN MỚI*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {user_id}\n"
            f"💵 Số tiền: {amount:,.0f} VND\n"
            f"🏦 {payment_method}: {account_number} ({account_name})\n"
            f"📋 Mã: #{withdrawal.id}"
        )

        logger.info(f"User {user_id} requested withdrawal #{withdrawal.id}: {amount}")
        return withdrawal

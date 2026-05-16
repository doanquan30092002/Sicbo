import logging
from decimal import Decimal
from typing import Optional

from app.application.ports.notification_port import INotificationPort
from app.domain.entities.wallet import Withdrawal
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import TransactionType, WithdrawalStatus

logger = logging.getLogger(__name__)


class ProcessWithdrawal:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        user_repo: IUserRepository,
        notification_port: INotificationPort,
    ):
        self._wallet_repo = wallet_repo
        self._user_repo = user_repo
        self._notification = notification_port

    async def approve(self, withdrawal_id: int, admin_id: int) -> Withdrawal:
        withdrawal = await self._wallet_repo.update_withdrawal_status(
            withdrawal_id,
            status=WithdrawalStatus.APPROVED,
            processed_by=admin_id,
        )
        user = await self._user_repo.get_by_id(withdrawal.user_id)
        if user and user.telegram_id:
            await self._notification.send_user_message(
                user.telegram_id,
                f"✅ Yêu cầu rút {withdrawal.amount:,.0f} VND của bạn đã được *duyệt*.\n"
                f"Tiền sẽ được chuyển trong thời gian sớm nhất.",
            )
        logger.info(f"Admin {admin_id} approved withdrawal #{withdrawal_id}")
        return withdrawal

    async def reject(self, withdrawal_id: int, admin_id: int, reason: Optional[str] = None) -> Withdrawal:
        withdrawal = await self._wallet_repo.update_withdrawal_status(
            withdrawal_id,
            status=WithdrawalStatus.REJECTED,
            admin_note=reason,
            processed_by=admin_id,
        )

        # Refund balance
        balance = await self._user_repo.get_balance_for_update(withdrawal.user_id)
        new_balance = balance + withdrawal.amount
        await self._user_repo.update_balance(withdrawal.user_id, new_balance)
        await self._wallet_repo.create_transaction(
            user_id=withdrawal.user_id,
            type=TransactionType.REFUND,
            amount=withdrawal.amount,
            balance_before=balance,
            balance_after=new_balance,
            description=f"Hoàn tiền rút #{withdrawal_id} bị từ chối",
        )

        user = await self._user_repo.get_by_id(withdrawal.user_id)
        if user and user.telegram_id:
            reason_text = f"\nLý do: {reason}" if reason else ""
            await self._notification.send_user_message(
                user.telegram_id,
                f"❌ Yêu cầu rút {withdrawal.amount:,.0f} VND bị *từ chối*."
                f"{reason_text}\n"
                f"💰 Số dư đã được hoàn: {new_balance:,.0f} VND",
            )
        logger.info(f"Admin {admin_id} rejected withdrawal #{withdrawal_id}: {reason}")
        return withdrawal

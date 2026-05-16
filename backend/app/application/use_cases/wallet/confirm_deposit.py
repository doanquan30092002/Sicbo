import logging
from decimal import Decimal

from app.application.ports.notification_port import INotificationPort
from app.domain.entities.wallet import Deposit
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import TransactionType

logger = logging.getLogger(__name__)


class DepositAlreadyConfirmedError(Exception):
    pass


class ConfirmDeposit:
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
        transfer_content: str,
        amount: Decimal,
        sepay_transaction_id: str,
    ) -> Deposit:
        deposit = await self._wallet_repo.get_deposit_by_transfer_content(transfer_content)
        if not deposit:
            logger.warning(f"SePay webhook: không tìm thấy deposit với code={transfer_content}")
            return None

        if deposit.status == "confirmed":
            raise DepositAlreadyConfirmedError(f"Deposit {deposit.id} đã được xác nhận rồi.")

        # Atomic: confirm deposit + credit balance + create transaction
        balance = await self._user_repo.get_balance_for_update(deposit.user_id)
        credit_amount = amount  # Credit đúng số tiền SePay nhận được
        new_balance = balance + credit_amount

        await self._user_repo.update_balance(deposit.user_id, new_balance)
        confirmed = await self._wallet_repo.confirm_deposit(deposit.id, sepay_transaction_id)
        await self._wallet_repo.create_transaction(
            user_id=deposit.user_id,
            type=TransactionType.DEPOSIT,
            amount=credit_amount,
            balance_before=balance,
            balance_after=new_balance,
            reference_id=sepay_transaction_id,
            description=f"Nạp tiền qua {deposit.payment_method}",
        )

        # Notify user
        user = await self._user_repo.get_by_id(deposit.user_id)
        if user and user.telegram_id:
            await self._notification.send_user_message(
                user.telegram_id,
                f"✅ Nạp tiền thành công!\n"
                f"💵 +{credit_amount:,.0f} VND\n"
                f"💰 Số dư: {new_balance:,.0f} VND",
            )

        logger.info(f"Confirmed deposit #{deposit.id} for user {deposit.user_id}: +{credit_amount}")
        return confirmed

import random
from decimal import Decimal

from app.domain.entities.wallet import Deposit
from app.domain.repositories.wallet_repo import IWalletRepository


class RequestDeposit:
    def __init__(self, wallet_repo: IWalletRepository, bank_account: str, momo_phone: str):
        self._wallet_repo = wallet_repo
        self._bank_account = bank_account
        self._momo_phone = momo_phone

    async def execute(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,  # "bank_transfer" | "momo"
    ) -> Deposit:
        if amount <= 0:
            raise ValueError("Số tiền nạp phải lớn hơn 0.")
        if amount % 1000 != 0:
            raise ValueError("Số tiền nạp phải là bội số của 1,000 VND.")

        transfer_content = self._generate_transfer_content(user_id)

        bank_account = self._bank_account if payment_method == "bank_transfer" else self._momo_phone

        return await self._wallet_repo.create_deposit(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            transfer_content=transfer_content,
            bank_account=bank_account,
        )

    def _generate_transfer_content(self, user_id: int) -> str:
        # Format: NAP + user_id (3 chữ số) + random 3 số
        # Ví dụ: NAP001042
        suffix = random.randint(100, 999)
        return f"NAP{user_id:03d}{suffix}"

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from app.domain.entities.wallet import Deposit, Transaction, Withdrawal


class IWalletRepository(ABC):
    @abstractmethod
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
    ) -> Transaction: ...

    @abstractmethod
    async def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Transaction], int]: ...

    @abstractmethod
    async def create_deposit(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        transfer_content: str,
        bank_account: Optional[str] = None,
    ) -> Deposit: ...

    @abstractmethod
    async def get_deposit_by_transfer_content(self, transfer_content: str) -> Optional[Deposit]: ...

    @abstractmethod
    async def get_deposit_by_id(self, deposit_id: int) -> Optional[Deposit]: ...

    @abstractmethod
    async def confirm_deposit(self, deposit_id: int, sepay_transaction_id: str) -> Deposit: ...

    @abstractmethod
    async def create_withdrawal(
        self,
        user_id: int,
        amount: Decimal,
        payment_method: str,
        account_number: str,
        account_name: str,
        bank_name: Optional[str] = None,
    ) -> Withdrawal: ...

    @abstractmethod
    async def get_pending_withdrawals(self, page: int = 1, limit: int = 20) -> tuple[list[Withdrawal], int]: ...

    @abstractmethod
    async def update_withdrawal_status(
        self,
        withdrawal_id: int,
        status: str,
        admin_note: Optional[str] = None,
        processed_by: Optional[int] = None,
    ) -> Withdrawal: ...

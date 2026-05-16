"""Unit tests cho RequestDeposit, ConfirmDeposit, RequestWithdrawal, ProcessWithdrawal."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.admin.process_withdrawal import ProcessWithdrawal
from app.application.use_cases.wallet.confirm_deposit import (
    ConfirmDeposit,
    DepositAlreadyConfirmedError,
)
from app.application.use_cases.wallet.request_deposit import RequestDeposit
from app.application.use_cases.wallet.request_withdrawal import (
    InsufficientBalanceError,
    RequestWithdrawal,
)
from app.domain.entities.user import User
from app.domain.entities.wallet import Deposit, Withdrawal
from app.domain.value_objects.bet_type import WithdrawalStatus


def _make_user(**overrides) -> User:
    base = dict(
        id=1, username="alice", password_hash="x",
        balance=Decimal("100000"), is_active=True, is_admin=False,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    base.update(overrides)
    return User(**base)


def _make_deposit(**overrides) -> Deposit:
    base = dict(
        id=5, user_id=1, amount=Decimal("100000"),
        payment_method="bank_transfer", transfer_content="NAP001123",
        status="pending", created_at=datetime.now(),
    )
    base.update(overrides)
    return Deposit(**base)


def _make_withdrawal(**overrides) -> Withdrawal:
    base = dict(
        id=7, user_id=1, amount=Decimal("100000"),
        payment_method="bank_transfer",
        account_number="0123456789", account_name="Alice",
        status="pending", requested_at=datetime.now(),
    )
    base.update(overrides)
    return Withdrawal(**base)


class TestRequestDeposit:
    async def test_creates_deposit_with_transfer_content(self):
        wallet_repo = AsyncMock()
        wallet_repo.create_deposit.return_value = _make_deposit()

        uc = RequestDeposit(wallet_repo, bank_account="12345", momo_phone="0901")
        await uc.execute(user_id=1, amount=Decimal("100000"), payment_method="bank_transfer")

        kwargs = wallet_repo.create_deposit.await_args.kwargs
        assert kwargs["transfer_content"].startswith("NAP001")
        assert kwargs["bank_account"] == "12345"

    async def test_momo_uses_phone_as_account(self):
        wallet_repo = AsyncMock()
        wallet_repo.create_deposit.return_value = _make_deposit()

        uc = RequestDeposit(wallet_repo, bank_account="12345", momo_phone="0901")
        await uc.execute(user_id=1, amount=Decimal("100000"), payment_method="momo")
        assert wallet_repo.create_deposit.await_args.kwargs["bank_account"] == "0901"

    async def test_zero_amount_rejected(self):
        wallet_repo = AsyncMock()
        uc = RequestDeposit(wallet_repo, "12345", "0901")
        with pytest.raises(ValueError):
            await uc.execute(1, Decimal(0), "bank_transfer")

    async def test_amount_not_multiple_of_1000_rejected(self):
        wallet_repo = AsyncMock()
        uc = RequestDeposit(wallet_repo, "12345", "0901")
        with pytest.raises(ValueError, match="1,000"):
            await uc.execute(1, Decimal("1500"), "bank_transfer")


class TestConfirmDeposit:
    async def test_credits_balance_and_confirms(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()

        deposit = _make_deposit()
        wallet_repo.get_deposit_by_transfer_content.return_value = deposit
        wallet_repo.confirm_deposit.return_value = deposit
        user_repo.get_balance_for_update.return_value = Decimal("0")
        user_repo.get_by_id.return_value = _make_user(telegram_id=None)

        uc = ConfirmDeposit(wallet_repo, user_repo, notif)
        await uc.execute("NAP001123", Decimal("100000"), "SEPAY-TX-1")

        user_repo.update_balance.assert_awaited_once_with(1, Decimal("100000"))
        wallet_repo.confirm_deposit.assert_awaited_once_with(5, "SEPAY-TX-1")
        wallet_repo.create_transaction.assert_awaited_once()

    async def test_already_confirmed_raises(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        wallet_repo.get_deposit_by_transfer_content.return_value = _make_deposit(status="confirmed")

        uc = ConfirmDeposit(wallet_repo, user_repo, notif)
        with pytest.raises(DepositAlreadyConfirmedError):
            await uc.execute("NAP001123", Decimal("100000"), "SEPAY-TX-1")
        user_repo.update_balance.assert_not_called()

    async def test_unknown_transfer_content_returns_none(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        wallet_repo.get_deposit_by_transfer_content.return_value = None

        uc = ConfirmDeposit(wallet_repo, user_repo, notif)
        result = await uc.execute("UNKNOWN", Decimal("100000"), "SEPAY-TX-1")
        assert result is None
        user_repo.update_balance.assert_not_called()


class TestRequestWithdrawal:
    async def test_deducts_balance_and_notifies_admin(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        user_repo.get_balance_for_update.return_value = Decimal("200000")
        wallet_repo.create_withdrawal.return_value = _make_withdrawal()

        uc = RequestWithdrawal(wallet_repo, user_repo, notif)
        await uc.execute(
            user_id=1, amount=Decimal("100000"), payment_method="bank_transfer",
            account_number="123", account_name="Alice",
        )

        user_repo.update_balance.assert_awaited_once_with(1, Decimal("100000"))
        notif.send_admin_message.assert_awaited_once()

    async def test_below_minimum_rejected(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        uc = RequestWithdrawal(wallet_repo, user_repo, notif)
        with pytest.raises(ValueError, match="tối thiểu"):
            await uc.execute(1, Decimal("10000"), "bank_transfer", "123", "Alice")

    async def test_insufficient_balance_rejected(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        user_repo.get_balance_for_update.return_value = Decimal("10000")
        uc = RequestWithdrawal(wallet_repo, user_repo, notif)
        with pytest.raises(InsufficientBalanceError):
            await uc.execute(1, Decimal("50000"), "bank_transfer", "123", "Alice")


class TestProcessWithdrawal:
    async def test_approve_updates_status_and_notifies(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        approved = _make_withdrawal(status=WithdrawalStatus.APPROVED.value)
        wallet_repo.update_withdrawal_status.return_value = approved
        user_repo.get_by_id.return_value = _make_user(telegram_id=12345)

        uc = ProcessWithdrawal(wallet_repo, user_repo, notif)
        await uc.approve(7, admin_id=99)

        notif.send_user_message.assert_awaited_once()
        # Approve KHÔNG được cộng lại balance
        user_repo.update_balance.assert_not_called()

    async def test_reject_refunds_balance(self):
        wallet_repo = AsyncMock()
        user_repo = AsyncMock()
        notif = AsyncMock()
        wallet_repo.update_withdrawal_status.return_value = _make_withdrawal(
            status=WithdrawalStatus.REJECTED.value
        )
        user_repo.get_balance_for_update.return_value = Decimal("0")
        user_repo.get_by_id.return_value = _make_user(telegram_id=12345)

        uc = ProcessWithdrawal(wallet_repo, user_repo, notif)
        await uc.reject(7, admin_id=99, reason="Sai thông tin")

        user_repo.update_balance.assert_awaited_once_with(1, Decimal("100000"))
        wallet_repo.create_transaction.assert_awaited_once()
        notif.send_user_message.assert_awaited_once()

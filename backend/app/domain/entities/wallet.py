from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    id: int
    user_id: int
    type: str  # deposit | withdraw | bet_debit | win_credit | refund
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str  # pending | completed | failed
    created_at: datetime
    reference_id: Optional[str] = None
    description: Optional[str] = None
    related_bet_id: Optional[int] = None


@dataclass
class Deposit:
    id: int
    user_id: int
    amount: Decimal
    payment_method: str  # bank_transfer | momo
    transfer_content: str
    status: str  # pending | confirmed | failed
    created_at: datetime
    bank_account: Optional[str] = None
    sepay_transaction_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None


@dataclass
class Withdrawal:
    id: int
    user_id: int
    amount: Decimal
    payment_method: str
    account_number: str
    account_name: str
    status: str  # pending | approved | rejected | completed
    requested_at: datetime
    bank_name: Optional[str] = None
    admin_note: Optional[str] = None
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None

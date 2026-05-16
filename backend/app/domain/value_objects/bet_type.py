from enum import Enum


class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    BET_DEBIT = "bet_debit"
    WIN_CREDIT = "win_credit"
    REFUND = "refund"


class DepositStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class WithdrawalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

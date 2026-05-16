from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "VND"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Insufficient funds")
        return Money(result, self.currency)

    def __mul__(self, multiplier: Decimal) -> "Money":
        return Money(self.amount * multiplier, self.currency)

    def __ge__(self, other: "Money") -> bool:
        return self.amount >= other.amount

    def __gt__(self, other: "Money") -> bool:
        return self.amount > other.amount

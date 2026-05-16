from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    balance: Decimal
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.session import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal(0))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone: Mapped[Optional[str]] = mapped_column(String(15), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

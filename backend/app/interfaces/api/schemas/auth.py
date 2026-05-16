"""Pydantic schemas cho auth endpoints."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    phone: Optional[str] = Field(default=None, max_length=15)
    email: Optional[str] = Field(default=None, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("Username chỉ chứa chữ, số và dấu gạch dưới.")
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    balance: Decimal
    is_active: bool
    is_admin: bool
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    created_at: datetime


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str


class TelegramLinkResponse(BaseModel):
    token: str
    expires_at: datetime

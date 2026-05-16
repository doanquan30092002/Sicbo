"""Tạo admin user đầu tiên cho Sicbo.

Usage:
    cd backend
    python -m scripts.seed_admin admin yourpassword123
    # hoặc set qua env:
    SEED_ADMIN_USERNAME=admin SEED_ADMIN_PASSWORD=xxx python -m scripts.seed_admin
"""
import asyncio
import os
import sys
from decimal import Decimal

from sqlalchemy import select

from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.session import AsyncSessionLocal
from app.utils.security import hash_password


async def seed_admin(username: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(UserModel).where(UserModel.username == username))
        if existing.scalar_one_or_none() is not None:
            print(f"[skip] User '{username}' already exists.")
            return

        user = UserModel(
            username=username,
            password_hash=hash_password(password),
            balance=Decimal(0),
            is_active=True,
            is_admin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"[ok] Created admin user: id={user.id}, username='{user.username}'")


def main() -> int:
    if len(sys.argv) >= 3:
        username, password = sys.argv[1], sys.argv[2]
    else:
        username = os.environ.get("SEED_ADMIN_USERNAME")
        password = os.environ.get("SEED_ADMIN_PASSWORD")
        if not username or not password:
            print("Usage: python -m scripts.seed_admin <username> <password>")
            print("   or: set SEED_ADMIN_USERNAME=... SEED_ADMIN_PASSWORD=... env vars")
            return 1

    if len(password) < 8:
        print("ERROR: password must be >= 8 characters.")
        return 1

    asyncio.run(seed_admin(username, password))
    return 0


if __name__ == "__main__":
    sys.exit(main())

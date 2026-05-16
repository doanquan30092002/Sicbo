"""Unit tests cho RegisterUser + LoginUser use cases."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.auth.login_user import InvalidCredentialsError, LoginUser
from app.application.use_cases.auth.register_user import RegisterUser, UserAlreadyExistsError
from app.domain.entities.user import User


def _make_user(**overrides) -> User:
    base = dict(
        id=1,
        username="alice",
        password_hash="hashed",
        balance=Decimal(0),
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    base.update(overrides)
    return User(**base)


class TestRegisterUser:
    async def test_register_new_user(self, monkeypatch):
        # Mock hash_password để tránh phụ thuộc bcrypt backend trong test
        from app.application.use_cases.auth import register_user as ru
        monkeypatch.setattr(ru, "hash_password", lambda p: f"hashed:{p}")

        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = None
        expected = _make_user()
        user_repo.create.return_value = expected

        uc = RegisterUser(user_repo)
        user = await uc.execute("alice", "pwd12345")

        assert user is expected
        user_repo.create.assert_awaited_once()
        # Password phải được hash, không truyền plain
        kwargs = user_repo.create.await_args.kwargs
        assert kwargs["password_hash"] != "pwd12345"
        assert kwargs["username"] == "alice"

    async def test_register_duplicate_username_raises(self):
        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = _make_user()

        uc = RegisterUser(user_repo)
        with pytest.raises(UserAlreadyExistsError):
            await uc.execute("alice", "pwd12345")

        user_repo.create.assert_not_called()


class TestLoginUser:
    async def test_login_with_correct_credentials(self, monkeypatch):
        from app.application.use_cases.auth import login_user as login_module
        monkeypatch.setattr(login_module, "verify_password", lambda p, h: True)
        monkeypatch.setattr(login_module, "create_access_token", lambda uid, admin: "access-token")
        monkeypatch.setattr(login_module, "create_refresh_token", lambda uid: "refresh-token")

        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = _make_user()

        uc = LoginUser(user_repo)
        user, access, refresh = await uc.execute("alice", "pwd12345")

        assert user.username == "alice"
        assert access == "access-token"
        assert refresh == "refresh-token"

    async def test_login_wrong_password_raises(self, monkeypatch):
        from app.application.use_cases.auth import login_user as login_module
        monkeypatch.setattr(login_module, "verify_password", lambda p, h: False)

        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = _make_user()

        uc = LoginUser(user_repo)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute("alice", "wrong-password")

    async def test_login_nonexistent_user_raises(self):
        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = None

        uc = LoginUser(user_repo)
        with pytest.raises(InvalidCredentialsError):
            await uc.execute("ghost", "anything")

    async def test_login_inactive_user_raises(self, monkeypatch):
        from app.application.use_cases.auth import login_user as login_module
        monkeypatch.setattr(login_module, "verify_password", lambda p, h: True)

        user_repo = AsyncMock()
        user_repo.get_by_username.return_value = _make_user(is_active=False)

        uc = LoginUser(user_repo)
        with pytest.raises(InvalidCredentialsError, match="khóa"):
            await uc.execute("alice", "pwd12345")

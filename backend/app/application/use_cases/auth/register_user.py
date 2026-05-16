from typing import Optional

from app.domain.entities.user import User
from app.domain.repositories.user_repo import IUserRepository
from app.utils.security import hash_password


class UserAlreadyExistsError(Exception):
    pass


class RegisterUser:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def execute(
        self,
        username: str,
        password: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        existing = await self._user_repo.get_by_username(username)
        if existing:
            raise UserAlreadyExistsError(f"Username '{username}' đã được sử dụng.")

        password_hash = hash_password(password)
        return await self._user_repo.create(
            username=username,
            password_hash=password_hash,
            phone=phone,
            email=email,
        )

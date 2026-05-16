from app.domain.entities.user import User
from app.domain.repositories.user_repo import IUserRepository
from app.utils.security import verify_password, create_access_token, create_refresh_token


class InvalidCredentialsError(Exception):
    pass


class LoginUser:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def execute(self, username: str, password: str) -> tuple[User, str, str]:
        """Returns (user, access_token, refresh_token)"""
        user = await self._user_repo.get_by_username(username)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Tên đăng nhập hoặc mật khẩu không đúng.")

        if not user.is_active:
            raise InvalidCredentialsError("Tài khoản đã bị khóa.")

        access_token = create_access_token(user.id, user.is_admin)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

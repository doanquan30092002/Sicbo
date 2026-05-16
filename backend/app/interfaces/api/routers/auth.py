"""Auth router — register, login, me, refresh."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.application.use_cases.auth.login_user import InvalidCredentialsError, LoginUser
from app.application.use_cases.auth.register_user import (
    RegisterUser,
    UserAlreadyExistsError,
)
from app.application.use_cases.auth.telegram_link import GenerateLinkToken
from app.domain.entities.user import User
from app.interfaces.api.dependencies import (
    get_current_user,
    get_generate_link_token_uc,
    get_login_user_uc,
    get_register_user_uc,
    get_user_repo,
)
from app.interfaces.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    TelegramLinkResponse,
    TokenPair,
    UserResponse,
)
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    uc: RegisterUser = Depends(get_register_user_uc),
):
    try:
        user = await uc.execute(
            username=body.username,
            password=body.password,
            phone=body.phone,
            email=body.email,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    uc: LoginUser = Depends(get_login_user_uc),
):
    try:
        user, access, refresh = await uc.execute(body.username, body.password)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return LoginResponse(
        user=UserResponse.model_validate(user, from_attributes=True),
        tokens=TokenPair(access_token=access, refresh_token=refresh),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repo),
):
    payload = decode_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ hoặc đã hết hạn.",
        )
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ.")

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User không tồn tại hoặc bị khóa.")

    return TokenPair(
        access_token=create_access_token(user.id, user.is_admin),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/telegram/link-token", response_model=TelegramLinkResponse)
async def create_telegram_link_token(
    user: User = Depends(get_current_user),
    uc: GenerateLinkToken = Depends(get_generate_link_token_uc),
):
    """Tạo 6-digit token để user nhập vào bot Telegram (lệnh /link <token>)."""
    token, expires_at = await uc.execute(user.id)
    return TelegramLinkResponse(token=token, expires_at=expires_at)

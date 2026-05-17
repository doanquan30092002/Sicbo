"""FastAPI dependency injection: session, repos, use cases, JWT auth."""
from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.admin.credit_user_balance import CreditUserBalance
from app.application.use_cases.admin.process_withdrawal import ProcessWithdrawal
from app.application.use_cases.auth.login_user import LoginUser
from app.application.use_cases.auth.register_user import RegisterUser
from app.application.use_cases.auth.telegram_link import (
    GenerateLinkToken,
    LinkTelegram,
)
from app.application.use_cases.betting.cancel_bet import CancelBet
from app.application.use_cases.betting.place_bet import PlaceBet
from app.application.use_cases.betting.settle_bets import SettleBets
from app.application.use_cases.lottery.fetch_and_store_result import FetchAndStoreResult
from app.application.use_cases.wallet.confirm_deposit import ConfirmDeposit
from app.application.use_cases.wallet.request_deposit import RequestDeposit
from app.application.use_cases.wallet.request_withdrawal import RequestWithdrawal
from app.config import settings
from app.domain.entities.user import User
from app.infrastructure.database.repositories.bet_repository import BetRepository
from app.infrastructure.database.repositories.game_result_repository import (
    GameResultRepository,
)
from app.infrastructure.database.repositories.telegram_link_repository import (
    TelegramLinkTokenRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.wallet_repository import WalletRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.external.sepay_gateway import SePayGateway
from app.infrastructure.external.xsmb_fetcher import XSMBFetcher
from app.infrastructure.notifications.telegram_notifier import TelegramNotifier
from app.utils.security import decode_access_token


# ---------- Session ----------

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Tạo 1 session per request; commit cuối cùng nếu không có exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------- Repositories ----------

def get_user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_bet_repo(session: AsyncSession = Depends(get_session)) -> BetRepository:
    return BetRepository(session)


def get_wallet_repo(session: AsyncSession = Depends(get_session)) -> WalletRepository:
    return WalletRepository(session)


def get_game_result_repo(session: AsyncSession = Depends(get_session)) -> GameResultRepository:
    return GameResultRepository(session)


def get_telegram_link_repo(
    session: AsyncSession = Depends(get_session),
) -> TelegramLinkTokenRepository:
    return TelegramLinkTokenRepository(session)


# ---------- Cross-cutting infra ----------

_telegram_notifier: Optional[TelegramNotifier] = None
_sepay_gateway: Optional[SePayGateway] = None
_xsmb_fetcher: Optional[XSMBFetcher] = None


def get_telegram_notifier() -> TelegramNotifier:
    global _telegram_notifier
    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier


def get_sepay_gateway() -> SePayGateway:
    global _sepay_gateway
    if _sepay_gateway is None:
        _sepay_gateway = SePayGateway()
    return _sepay_gateway


def get_xsmb_fetcher() -> XSMBFetcher:
    global _xsmb_fetcher
    if _xsmb_fetcher is None:
        _xsmb_fetcher = XSMBFetcher()
    return _xsmb_fetcher


# ---------- Use cases ----------

def get_register_user_uc(
    user_repo: UserRepository = Depends(get_user_repo),
) -> RegisterUser:
    return RegisterUser(user_repo)


def get_login_user_uc(
    user_repo: UserRepository = Depends(get_user_repo),
) -> LoginUser:
    return LoginUser(user_repo)


def get_place_bet_uc(
    bet_repo: BetRepository = Depends(get_bet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
) -> PlaceBet:
    return PlaceBet(bet_repo, user_repo, wallet_repo)


def get_cancel_bet_uc(
    bet_repo: BetRepository = Depends(get_bet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
) -> CancelBet:
    return CancelBet(bet_repo, user_repo, wallet_repo)


def get_settle_bets_uc(
    bet_repo: BetRepository = Depends(get_bet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    game_result_repo: GameResultRepository = Depends(get_game_result_repo),
    notifier: TelegramNotifier = Depends(get_telegram_notifier),
) -> SettleBets:
    return SettleBets(bet_repo, game_result_repo, user_repo, wallet_repo, notifier)


def get_fetch_result_uc(
    game_result_repo: GameResultRepository = Depends(get_game_result_repo),
    fetcher: XSMBFetcher = Depends(get_xsmb_fetcher),
) -> FetchAndStoreResult:
    return FetchAndStoreResult(game_result_repo, fetcher)


def get_request_deposit_uc(
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
) -> RequestDeposit:
    return RequestDeposit(
        wallet_repo, settings.bank_account_no, settings.momo_phone
    )


def get_confirm_deposit_uc(
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    notifier: TelegramNotifier = Depends(get_telegram_notifier),
) -> ConfirmDeposit:
    return ConfirmDeposit(wallet_repo, user_repo, notifier)


def get_request_withdrawal_uc(
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    notifier: TelegramNotifier = Depends(get_telegram_notifier),
) -> RequestWithdrawal:
    return RequestWithdrawal(wallet_repo, user_repo, notifier)


def get_process_withdrawal_uc(
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    notifier: TelegramNotifier = Depends(get_telegram_notifier),
) -> ProcessWithdrawal:
    return ProcessWithdrawal(wallet_repo, user_repo, notifier)


def get_credit_user_balance_uc(
    wallet_repo: WalletRepository = Depends(get_wallet_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    notifier: TelegramNotifier = Depends(get_telegram_notifier),
) -> CreditUserBalance:
    return CreditUserBalance(wallet_repo, user_repo, notifier)


def get_generate_link_token_uc(
    token_repo: TelegramLinkTokenRepository = Depends(get_telegram_link_repo),
) -> GenerateLinkToken:
    return GenerateLinkToken(token_repo)


def get_link_telegram_uc(
    token_repo: TelegramLinkTokenRepository = Depends(get_telegram_link_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> LinkTelegram:
    return LinkTelegram(token_repo, user_repo)


# ---------- Auth dependencies ----------

async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu hoặc sai header Authorization.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[len("Bearer "):].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
        )
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ.")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User không tồn tại.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa.")
    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yêu cầu quyền admin.")
    return user

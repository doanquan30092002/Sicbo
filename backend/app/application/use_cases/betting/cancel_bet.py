import logging
from datetime import datetime
from decimal import Decimal

import pytz

from app.domain.entities.bet import Bet
from app.domain.games.registry import GameRegistry
from app.domain.repositories.bet_repo import IBetRepository
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import BetStatus, TransactionType

logger = logging.getLogger(__name__)

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


class BetNotCancellableError(Exception):
    pass


class CancelBet:
    def __init__(
        self,
        bet_repo: IBetRepository,
        user_repo: IUserRepository,
        wallet_repo: IWalletRepository,
    ):
        self._bet_repo = bet_repo
        self._user_repo = user_repo
        self._wallet_repo = wallet_repo

    async def execute(self, user_id: int, bet_id: int) -> Bet:
        bet = await self._bet_repo.get_by_id(bet_id)
        if not bet or bet.user_id != user_id:
            raise BetNotCancellableError("Lệnh cược không tồn tại.")

        if bet.status != BetStatus.PENDING:
            raise BetNotCancellableError("Chỉ có thể hủy lệnh cược đang chờ kết quả.")

        game = GameRegistry.get(bet.game_id)
        now_vn = datetime.now(VN_TZ)
        cutoff_dt = VN_TZ.localize(
            datetime.combine(bet.draw_date, game.cutoff_time)
        )
        if now_vn >= cutoff_dt:
            raise BetNotCancellableError("Đã quá giờ, không thể hủy lệnh cược.")

        # Refund + cancel
        balance = await self._user_repo.get_balance_for_update(user_id)
        new_balance = balance + bet.total_stake
        await self._user_repo.update_balance(user_id, new_balance)

        cancelled_bet = await self._bet_repo.cancel(bet_id)

        await self._wallet_repo.create_transaction(
            user_id=user_id,
            type=TransactionType.REFUND,
            amount=bet.total_stake,
            balance_before=balance,
            balance_after=new_balance,
            description=f"Hủy lệnh cược #{bet_id}",
            related_bet_id=bet_id,
        )

        logger.info(f"User {user_id} cancelled bet #{bet_id}, refunded {bet.total_stake}")
        return cancelled_bet

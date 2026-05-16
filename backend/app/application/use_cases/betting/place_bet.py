import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import pytz

from app.domain.entities.bet import Bet
from app.domain.games.registry import GameRegistry
from app.domain.repositories.bet_repo import IBetRepository
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import TransactionType

logger = logging.getLogger(__name__)

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


class CutoffPassedError(Exception):
    pass


class InsufficientBalanceError(Exception):
    pass


class PlaceBet:
    def __init__(
        self,
        bet_repo: IBetRepository,
        user_repo: IUserRepository,
        wallet_repo: IWalletRepository,
    ):
        self._bet_repo = bet_repo
        self._user_repo = user_repo
        self._wallet_repo = wallet_repo

    async def execute(
        self,
        user_id: int,
        game_id: str,
        bet_type_id: str,
        numbers: list[str],
        stake_per_point: Decimal,
        points: int,
        source: str = "web",
    ) -> Bet:
        game = GameRegistry.get(game_id)

        # Server-side cutoff check
        now_vn = datetime.now(VN_TZ)
        today = now_vn.date()
        cutoff_dt = VN_TZ.localize(
            datetime.combine(today, game.cutoff_time)
        )
        if now_vn >= cutoff_dt:
            raise CutoffPassedError(
                f"Đã hết giờ đặt cược {game.game_name}. "
                f"Cutoff: {game.cutoff_time.strftime('%H:%M')}."
            )

        # Validate bet input
        game.validate_bet(bet_type_id, numbers, stake_per_point)

        total_stake = stake_per_point * points
        bet_type_def = game.get_bet_type(bet_type_id)
        potential_win = stake_per_point * bet_type_def.odds * points

        # Atomic: balance check + deduct + create bet + create transaction
        balance = await self._user_repo.get_balance_for_update(user_id)
        if balance < total_stake:
            raise InsufficientBalanceError(
                f"Số dư không đủ. Cần {total_stake:,.0f} VND, hiện có {balance:,.0f} VND."
            )

        new_balance = balance - total_stake
        await self._user_repo.update_balance(user_id, new_balance)

        bet = await self._bet_repo.create(
            user_id=user_id,
            game_id=game_id,
            draw_date=today,
            bet_type_id=bet_type_id,
            numbers=[n.zfill(2) for n in numbers],
            stake_per_point=stake_per_point,
            points=points,
            total_stake=total_stake,
            potential_win=potential_win,
            source=source,
        )

        await self._wallet_repo.create_transaction(
            user_id=user_id,
            type=TransactionType.BET_DEBIT,
            amount=total_stake,
            balance_before=balance,
            balance_after=new_balance,
            description=f"Đặt cược {game.game_name} - {bet_type_id} #{bet.id}",
            related_bet_id=bet.id,
        )

        logger.info(f"User {user_id} placed bet #{bet.id}: {game_id}/{bet_type_id} {numbers} x{points}")
        return bet

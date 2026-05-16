import logging
from datetime import date
from decimal import Decimal

from app.application.ports.notification_port import INotificationPort
from app.domain.entities.bet import Bet
from app.domain.games.registry import GameRegistry
from app.domain.repositories.bet_repo import IBetRepository
from app.domain.repositories.game_result_repo import IGameResultRepository
from app.domain.repositories.user_repo import IUserRepository
from app.domain.repositories.wallet_repo import IWalletRepository
from app.domain.value_objects.bet_type import BetStatus, TransactionType

logger = logging.getLogger(__name__)


class SettleBets:
    def __init__(
        self,
        bet_repo: IBetRepository,
        game_result_repo: IGameResultRepository,
        user_repo: IUserRepository,
        wallet_repo: IWalletRepository,
        notification_port: INotificationPort,
    ):
        self._bet_repo = bet_repo
        self._game_result_repo = game_result_repo
        self._user_repo = user_repo
        self._wallet_repo = wallet_repo
        self._notification = notification_port

    async def execute(self, game_id: str, draw_date: date) -> dict:
        """
        Tính thắng/thua và trả tiền cho tất cả bets của game_id vào ngày draw_date.
        Returns stats: {total_bets, won_count, lost_count, total_payout}
        """
        result = await self._game_result_repo.get_by_game_and_date(game_id, draw_date)
        if not result:
            logger.error(f"Không có kết quả cho {game_id} ngày {draw_date}. Settlement bị bỏ qua.")
            return {"error": "no_result"}

        game = GameRegistry.get(game_id)
        bets = await self._bet_repo.get_pending_bets_for_settlement(game_id, draw_date)

        stats = {"total_bets": len(bets), "won_count": 0, "lost_count": 0, "total_payout": Decimal(0)}

        # Group bets by user để gửi 1 thông báo tổng hợp
        user_summaries: dict[int, dict] = {}

        for bet in bets:
            try:
                won, win_amount = game.evaluate_bet(
                    bet.bet_type_id, bet.numbers, bet.total_stake, result
                )

                if won:
                    # Atomic: credit balance + update bet status
                    balance = await self._user_repo.get_balance_for_update(bet.user_id)
                    new_balance = balance + win_amount
                    await self._user_repo.update_balance(bet.user_id, new_balance)
                    await self._wallet_repo.create_transaction(
                        user_id=bet.user_id,
                        type=TransactionType.WIN_CREDIT,
                        amount=win_amount,
                        balance_before=balance,
                        balance_after=new_balance,
                        description=f"Thắng cược {game.game_name} #{bet.id}",
                        related_bet_id=bet.id,
                    )
                    stats["won_count"] += 1
                    stats["total_payout"] += win_amount
                else:
                    stats["lost_count"] += 1

                await self._bet_repo.update_status(
                    bet.id,
                    BetStatus.WON if won else BetStatus.LOST,
                    win_amount,
                )

                # Tích lũy summary cho user
                uid = bet.user_id
                if uid not in user_summaries:
                    user_summaries[uid] = {"won": [], "lost": [], "total_win": Decimal(0), "total_stake": Decimal(0)}
                if won:
                    user_summaries[uid]["won"].append(bet)
                    user_summaries[uid]["total_win"] += win_amount
                else:
                    user_summaries[uid]["lost"].append(bet)
                user_summaries[uid]["total_stake"] += bet.total_stake

            except Exception as e:
                logger.error(f"Lỗi settle bet #{bet.id}: {e}")

        # Gửi thông báo tổng hợp cho từng user
        await self._notify_users(user_summaries)

        logger.info(f"Settled {game_id}/{draw_date}: {stats}")
        return stats

    async def _notify_users(self, user_summaries: dict) -> None:
        for user_id, summary in user_summaries.items():
            user = await self._user_repo.get_by_id(user_id)
            if not user or not user.telegram_id:
                continue

            won_count = len(summary["won"])
            lost_count = len(summary["lost"])
            total_win = summary["total_win"]
            total_stake = summary["total_stake"]
            net = total_win - total_stake

            balance = await self._user_repo.get_by_id(user_id)
            current_balance = balance.balance if balance else Decimal(0)

            lines = ["📊 *KẾT QUẢ HÔM NAY*", "━━━━━━━━━━━━━━━━━━"]
            if won_count:
                lines.append(f"✅ Thắng: {won_count} lệnh — +{total_win:,.0f} VND")
            if lost_count:
                lines.append(f"❌ Thua: {lost_count} lệnh")
            lines.append(f"💰 Số dư: {current_balance:,.0f} VND")

            await self._notification.send_user_message(user.telegram_id, "\n".join(lines))

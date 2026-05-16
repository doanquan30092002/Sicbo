"""Unit tests cho PlaceBet, CancelBet, SettleBets."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
import pytz

from app.application.use_cases.betting.cancel_bet import BetNotCancellableError, CancelBet
from app.application.use_cases.betting.place_bet import (
    CutoffPassedError,
    InsufficientBalanceError,
    PlaceBet,
)
from app.application.use_cases.betting.settle_bets import SettleBets
from app.domain.entities.bet import Bet
from app.domain.entities.game_result import GameResult
from app.domain.entities.user import User
from app.domain.games.registry import GameRegistry
from app.domain.value_objects.bet_type import BetStatus

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def _make_bet(**overrides) -> Bet:
    base = dict(
        id=10,
        user_id=1,
        game_id="xsmb",
        draw_date=date.today(),
        bet_type_id="lo",
        numbers=["23"],
        stake_per_point=Decimal("1000"),
        points=1,
        total_stake=Decimal("1000"),
        potential_win=Decimal("75000"),
        status=BetStatus.PENDING.value,
        win_amount=Decimal(0),
        placed_at=datetime.now(),
        source="web",
    )
    base.update(overrides)
    return Bet(**base)


def _make_user(**overrides) -> User:
    base = dict(
        id=1,
        username="alice",
        password_hash="x",
        balance=Decimal("100000"),
        is_active=True,
        is_admin=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    base.update(overrides)
    return User(**base)


@pytest.fixture
def now_before_cutoff(monkeypatch):
    """Patch datetime.now() trong place_bet/cancel_bet modules để trả về 10:00 sáng VN."""
    from app.application.use_cases.betting import place_bet as pb
    from app.application.use_cases.betting import cancel_bet as cb

    fixed = VN_TZ.localize(datetime.combine(date.today(), time(10, 0)))

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return fixed

        @staticmethod
        def combine(d, t):
            return datetime.combine(d, t)

    monkeypatch.setattr(pb, "datetime", FakeDT)
    monkeypatch.setattr(cb, "datetime", FakeDT)


@pytest.fixture
def now_after_cutoff(monkeypatch):
    """Patch datetime.now() để trả về 19:00 (sau cutoff 18:10)."""
    from app.application.use_cases.betting import place_bet as pb
    from app.application.use_cases.betting import cancel_bet as cb

    fixed = VN_TZ.localize(datetime.combine(date.today(), time(19, 0)))

    class FakeDT:
        @staticmethod
        def now(tz=None):
            return fixed

        @staticmethod
        def combine(d, t):
            return datetime.combine(d, t)

    monkeypatch.setattr(pb, "datetime", FakeDT)
    monkeypatch.setattr(cb, "datetime", FakeDT)


class TestPlaceBet:
    async def test_place_bet_success_lo(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()

        user_repo.get_balance_for_update.return_value = Decimal("100000")
        bet_repo.create.return_value = _make_bet()

        uc = PlaceBet(bet_repo, user_repo, wallet_repo)
        await uc.execute(
            user_id=1,
            game_id="xsmb",
            bet_type_id="lo",
            numbers=["23"],
            stake_per_point=Decimal("1000"),
            points=1,
        )

        # Trừ balance đúng
        user_repo.update_balance.assert_awaited_once_with(1, Decimal("99000"))
        bet_repo.create.assert_awaited_once()
        wallet_repo.create_transaction.assert_awaited_once()

    async def test_place_bet_insufficient_balance(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        user_repo.get_balance_for_update.return_value = Decimal("500")

        uc = PlaceBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(InsufficientBalanceError):
            await uc.execute(
                user_id=1,
                game_id="xsmb",
                bet_type_id="lo",
                numbers=["23"],
                stake_per_point=Decimal("1000"),
                points=1,
            )
        bet_repo.create.assert_not_called()
        user_repo.update_balance.assert_not_called()

    async def test_place_bet_after_cutoff_raises(self, now_after_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()

        uc = PlaceBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(CutoffPassedError):
            await uc.execute(
                user_id=1,
                game_id="xsmb",
                bet_type_id="lo",
                numbers=["23"],
                stake_per_point=Decimal("1000"),
                points=1,
            )
        # KHÔNG được trừ tiền nếu cutoff đã qua
        user_repo.get_balance_for_update.assert_not_called()

    async def test_place_bet_invalid_input_raises(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()

        uc = PlaceBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(ValueError):
            await uc.execute(
                user_id=1,
                game_id="xsmb",
                bet_type_id="xien2",
                numbers=["23"],  # cần 2 số
                stake_per_point=Decimal("1000"),
                points=1,
            )

    async def test_place_bet_normalizes_numbers_to_two_digits(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        user_repo.get_balance_for_update.return_value = Decimal("100000")
        bet_repo.create.return_value = _make_bet()

        uc = PlaceBet(bet_repo, user_repo, wallet_repo)
        await uc.execute(
            user_id=1,
            game_id="xsmb",
            bet_type_id="lo",
            numbers=["5"],
            stake_per_point=Decimal("1000"),
            points=1,
        )

        kwargs = bet_repo.create.await_args.kwargs
        assert kwargs["numbers"] == ["05"]


class TestCancelBet:
    async def test_cancel_pending_bet_before_cutoff(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()

        bet = _make_bet()
        bet_repo.get_by_id.return_value = bet
        bet_repo.cancel.return_value = bet
        user_repo.get_balance_for_update.return_value = Decimal("50000")

        uc = CancelBet(bet_repo, user_repo, wallet_repo)
        await uc.execute(user_id=1, bet_id=10)

        # Hoàn lại 1000 vào balance
        user_repo.update_balance.assert_awaited_once_with(1, Decimal("51000"))
        bet_repo.cancel.assert_awaited_once_with(10)
        wallet_repo.create_transaction.assert_awaited_once()

    async def test_cancel_other_users_bet_rejected(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        bet_repo.get_by_id.return_value = _make_bet(user_id=999)

        uc = CancelBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(BetNotCancellableError):
            await uc.execute(user_id=1, bet_id=10)

    async def test_cancel_already_settled_bet_rejected(self, now_before_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        bet_repo.get_by_id.return_value = _make_bet(status=BetStatus.WON.value)

        uc = CancelBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(BetNotCancellableError, match="đang chờ"):
            await uc.execute(user_id=1, bet_id=10)

    async def test_cancel_after_cutoff_rejected(self, now_after_cutoff):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        bet_repo.get_by_id.return_value = _make_bet()

        uc = CancelBet(bet_repo, user_repo, wallet_repo)
        with pytest.raises(BetNotCancellableError, match="quá giờ"):
            await uc.execute(user_id=1, bet_id=10)


class TestSettleBets:
    async def test_settle_no_result_returns_error(self):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        result_repo = AsyncMock()
        notif = AsyncMock()
        result_repo.get_by_game_and_date.return_value = None

        uc = SettleBets(bet_repo, result_repo, user_repo, wallet_repo, notif)
        out = await uc.execute("xsmb", date.today())

        assert out == {"error": "no_result"}
        bet_repo.update_status.assert_not_called()

    async def test_settle_winning_bet_credits_balance(self):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        result_repo = AsyncMock()
        notif = AsyncMock()

        # Setup: kết quả có "23" 1 lần → Lô thắng 75 * 1000 = 75000
        parsed = {
            "special_last2": "23",
            "all_last2": ["23", "45", "67"],
            "special_prize": "12323",
            "prizes": {},
        }
        result_repo.get_by_game_and_date.return_value = GameResult(
            id=1, game_id="xsmb", draw_date=date.today(),
            parsed_data=parsed, raw_json="{}", fetched_at=datetime.now(),
        )
        bet = _make_bet(numbers=["23"], total_stake=Decimal("1000"))
        bet_repo.get_pending_bets_for_settlement.return_value = [bet]
        user_repo.get_balance_for_update.return_value = Decimal("10000")
        user_repo.get_by_id.return_value = _make_user(telegram_id=None)

        uc = SettleBets(bet_repo, result_repo, user_repo, wallet_repo, notif)
        stats = await uc.execute("xsmb", date.today())

        assert stats["won_count"] == 1
        assert stats["lost_count"] == 0
        assert stats["total_payout"] == Decimal("75000")
        user_repo.update_balance.assert_awaited_once_with(1, Decimal("85000"))
        bet_repo.update_status.assert_awaited_once()
        call_kwargs = bet_repo.update_status.await_args.args
        assert call_kwargs[1] == BetStatus.WON

    async def test_settle_losing_bet_no_balance_change(self):
        bet_repo = AsyncMock()
        user_repo = AsyncMock()
        wallet_repo = AsyncMock()
        result_repo = AsyncMock()
        notif = AsyncMock()

        parsed = {"special_last2": "55", "all_last2": ["55"], "special_prize": "12355", "prizes": {}}
        result_repo.get_by_game_and_date.return_value = GameResult(
            id=1, game_id="xsmb", draw_date=date.today(),
            parsed_data=parsed, raw_json="{}", fetched_at=datetime.now(),
        )
        bet = _make_bet(numbers=["23"])
        bet_repo.get_pending_bets_for_settlement.return_value = [bet]
        user_repo.get_by_id.return_value = _make_user(telegram_id=None)

        uc = SettleBets(bet_repo, result_repo, user_repo, wallet_repo, notif)
        stats = await uc.execute("xsmb", date.today())

        assert stats["lost_count"] == 1
        assert stats["won_count"] == 0
        user_repo.update_balance.assert_not_called()
        bet_repo.update_status.assert_awaited_once()
        assert bet_repo.update_status.await_args.args[1] == BetStatus.LOST

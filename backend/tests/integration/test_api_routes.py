"""Integration tests cho FastAPI routes — dùng dependency_overrides + in-memory fakes.

Mục đích: verify router wiring, auth flow, request/response shape.
KHÔNG cần thật DB — overrides chèn fake repos.
"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.bet import Bet
from app.domain.entities.user import User
from app.interfaces.api import dependencies as deps
from app.interfaces.api.main import app
from app.utils.security import create_access_token


def _user(**kw) -> User:
    base = dict(
        id=1, username="alice", password_hash="x",
        balance=Decimal("100000"), is_active=True, is_admin=False,
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    base.update(kw)
    return User(**base)


def _bet(**kw) -> Bet:
    base = dict(
        id=42, user_id=1, game_id="xsmb", draw_date=date.today(),
        bet_type_id="lo", numbers=["23"],
        stake_per_point=Decimal("1000"), points=1,
        total_stake=Decimal("1000"), potential_win=Decimal("75000"),
        status="pending", win_amount=Decimal(0),
        placed_at=datetime.now(), source="web",
    )
    base.update(kw)
    return Bet(**base)


@pytest.fixture
def fake_user_repo():
    repo = AsyncMock()
    repo.get_by_id.return_value = _user()
    return repo


@pytest.fixture
def client(fake_user_repo, monkeypatch):
    # Mock hash_password để skip bcrypt
    from app.application.use_cases.auth import register_user as ru
    monkeypatch.setattr(ru, "hash_password", lambda p: f"hashed:{p}")

    app.dependency_overrides[deps.get_user_repo] = lambda: fake_user_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- Public endpoints ----------

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestGamesEndpoint:
    def test_list_active_games(self, client):
        r = client.get("/api/games")
        assert r.status_code == 200
        games = r.json()
        ids = [g["game_id"] for g in games]
        assert "xsmb" in ids
        xsmb = next(g for g in games if g["game_id"] == "xsmb")
        assert xsmb["cutoff_time"] == "18:10"
        assert len(xsmb["bet_types"]) == 4

    def test_cutoff_status(self, client):
        r = client.get("/api/games/xsmb/cutoff-status")
        assert r.status_code == 200
        body = r.json()
        assert body["game_id"] == "xsmb"
        assert body["cutoff_time"] == "18:10"
        assert "seconds_until_cutoff" in body

    def test_cutoff_unknown_game(self, client):
        r = client.get("/api/games/foo/cutoff-status")
        assert r.status_code == 404


# ---------- Auth ----------

class TestAuthRegister:
    def test_register_success(self, client, fake_user_repo):
        fake_user_repo.get_by_username.return_value = None
        fake_user_repo.create.return_value = _user(username="bob")

        r = client.post("/api/auth/register", json={
            "username": "bob",
            "password": "pwd12345",
        })
        assert r.status_code == 201
        assert r.json()["username"] == "bob"

    def test_register_duplicate_username(self, client, fake_user_repo):
        fake_user_repo.get_by_username.return_value = _user()

        r = client.post("/api/auth/register", json={
            "username": "alice",
            "password": "pwd12345",
        })
        assert r.status_code == 409

    def test_register_invalid_short_password(self, client):
        r = client.post("/api/auth/register", json={
            "username": "alice", "password": "123",
        })
        assert r.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client, fake_user_repo, monkeypatch):
        from app.application.use_cases.auth import login_user as lu
        monkeypatch.setattr(lu, "verify_password", lambda p, h: True)
        fake_user_repo.get_by_username.return_value = _user()

        r = client.post("/api/auth/login", json={
            "username": "alice", "password": "any",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["username"] == "alice"
        assert "access_token" in body["tokens"]
        assert "refresh_token" in body["tokens"]

    def test_login_wrong_password(self, client, fake_user_repo, monkeypatch):
        from app.application.use_cases.auth import login_user as lu
        monkeypatch.setattr(lu, "verify_password", lambda p, h: False)
        fake_user_repo.get_by_username.return_value = _user()

        r = client.post("/api/auth/login", json={
            "username": "alice", "password": "wrong",
        })
        assert r.status_code == 401


class TestAuthMe:
    def test_me_requires_token(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_with_valid_token(self, client, fake_user_repo):
        token = create_access_token(user_id=1, is_admin=False)
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_me_with_invalid_token(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401


# ---------- Bets ----------

class TestBetsRoutes:
    def test_place_bet_requires_auth(self, client):
        r = client.post("/api/bets", json={
            "game_id": "xsmb", "bet_type_id": "lo",
            "numbers": ["23"], "stake_per_point": "1000",
        })
        assert r.status_code == 401

    def test_place_bet_success(self, client, fake_user_repo, monkeypatch):
        # Patch datetime trong place_bet để cutoff luôn chưa qua
        from app.application.use_cases.betting import place_bet as pb
        import pytz
        VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
        fixed = VN_TZ.localize(datetime.combine(date.today(), datetime.min.time().replace(hour=10)))

        class FakeDT:
            @staticmethod
            def now(tz=None): return fixed
            @staticmethod
            def combine(d, t): return datetime.combine(d, t)
        monkeypatch.setattr(pb, "datetime", FakeDT)

        # Mock repos
        fake_bet_repo = AsyncMock()
        fake_bet_repo.create.return_value = _bet()
        fake_wallet_repo = AsyncMock()
        fake_user_repo.get_balance_for_update.return_value = Decimal("100000")

        app.dependency_overrides[deps.get_bet_repo] = lambda: fake_bet_repo
        app.dependency_overrides[deps.get_wallet_repo] = lambda: fake_wallet_repo

        token = create_access_token(user_id=1, is_admin=False)
        r = client.post(
            "/api/bets",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "game_id": "xsmb", "bet_type_id": "lo",
                "numbers": ["23"], "stake_per_point": "1000", "points": 1,
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["bet_type_id"] == "lo"

    def test_list_my_bets(self, client, fake_user_repo):
        fake_bet_repo = AsyncMock()
        fake_bet_repo.get_user_bets.return_value = ([_bet()], 1)
        app.dependency_overrides[deps.get_bet_repo] = lambda: fake_bet_repo

        token = create_access_token(user_id=1, is_admin=False)
        r = client.get("/api/bets", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1

    def test_get_bet_of_other_user_404(self, client, fake_user_repo):
        fake_bet_repo = AsyncMock()
        fake_bet_repo.get_by_id.return_value = _bet(user_id=999)
        app.dependency_overrides[deps.get_bet_repo] = lambda: fake_bet_repo

        token = create_access_token(user_id=1, is_admin=False)
        r = client.get("/api/bets/42", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404


# ---------- Results ----------

class TestResultsRoutes:
    def test_today_not_found(self, client):
        fake_repo = AsyncMock()
        fake_repo.get_by_game_and_date.return_value = None
        app.dependency_overrides[deps.get_game_result_repo] = lambda: fake_repo

        r = client.get("/api/results/xsmb/today")
        assert r.status_code == 404


# ---------- Wallet ----------

def _deposit(**kw):
    from app.domain.entities.wallet import Deposit
    base = dict(
        id=1, user_id=1, amount=Decimal("100000"),
        payment_method="bank_transfer", transfer_content="NAP001123",
        status="pending", created_at=datetime.now(),
        bank_account="123456", sepay_transaction_id=None, confirmed_at=None,
    )
    base.update(kw)
    return Deposit(**base)


def _withdrawal(**kw):
    from app.domain.entities.wallet import Withdrawal
    base = dict(
        id=1, user_id=1, amount=Decimal("100000"),
        payment_method="bank_transfer", account_number="9876543210",
        account_name="ALICE", bank_name="Vietcombank",
        status="pending", requested_at=datetime.now(),
        admin_note=None, processed_by=None, processed_at=None,
    )
    base.update(kw)
    return Withdrawal(**base)


class TestWalletRoutes:
    def test_init_deposit_success(self, client, fake_user_repo):
        fake_wallet_repo = AsyncMock()
        fake_wallet_repo.create_deposit.return_value = _deposit(amount=Decimal("100000"))
        app.dependency_overrides[deps.get_wallet_repo] = lambda: fake_wallet_repo

        token = create_access_token(user_id=1, is_admin=False)
        r = client.post(
            "/api/wallet/deposit/init",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": "100000", "payment_method": "bank_transfer"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["amount"] == "100000"
        assert body["transfer_content"].startswith("NAP")

    def test_init_deposit_invalid_amount(self, client):
        token = create_access_token(user_id=1, is_admin=False)
        r = client.post(
            "/api/wallet/deposit/init",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": "1234", "payment_method": "bank_transfer"},  # not multiple of 1000
        )
        assert r.status_code == 400

    def test_balance_requires_auth(self, client):
        r = client.get("/api/wallet/balance")
        assert r.status_code == 401

    def test_balance_success(self, client, fake_user_repo):
        token = create_access_token(user_id=1, is_admin=False)
        r = client.get("/api/wallet/balance", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert Decimal(str(body["balance"])) == Decimal("100000")
        assert body["user_id"] == 1

    def test_withdraw_below_min(self, client):
        token = create_access_token(user_id=1, is_admin=False)
        r = client.post(
            "/api/wallet/withdraw",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": "10000",
                "payment_method": "bank_transfer",
                "account_number": "9876543210",
                "account_name": "ALICE",
                "bank_name": "Vietcombank",
            },
        )
        assert r.status_code == 422  # Pydantic ge=50000


# ---------- Admin ----------

class TestAdminRoutes:
    def test_pending_requires_admin(self, client, fake_user_repo):
        # User is not admin → 403
        token = create_access_token(user_id=1, is_admin=False)
        r = client.get(
            "/api/admin/withdrawals/pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

    def test_pending_lists_for_admin(self, client, fake_user_repo):
        fake_user_repo.get_by_id.return_value = _user(is_admin=True)
        fake_wallet_repo = AsyncMock()
        fake_wallet_repo.get_pending_withdrawals.return_value = ([_withdrawal()], 1)
        app.dependency_overrides[deps.get_wallet_repo] = lambda: fake_wallet_repo

        token = create_access_token(user_id=1, is_admin=True)
        r = client.get(
            "/api/admin/withdrawals/pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == 1


# ---------- Webhooks ----------

class TestSepayWebhook:
    def test_rejects_without_signature(self, client):
        r = client.post("/api/webhooks/sepay", json={"transferType": "in", "transferAmount": "10000", "content": "NAP001123"})
        assert r.status_code == 401

    def test_skips_outgoing(self, client, monkeypatch):
        from app.infrastructure.external import sepay_gateway as sg

        class FakeGateway:
            def verify_webhook_signature(self, body, sig): return True

        app.dependency_overrides[deps.get_sepay_gateway] = lambda: FakeGateway()
        r = client.post(
            "/api/webhooks/sepay",
            headers={"X-Signature": "any"},
            json={"transferType": "out", "transferAmount": "10000", "content": "NAP001123"},
        )
        assert r.status_code == 200
        assert r.json()["skipped"] is True

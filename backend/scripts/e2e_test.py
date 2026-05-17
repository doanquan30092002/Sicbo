"""End-to-end smoke test cho toàn bộ Sicbo API."""
import sys
import time
from decimal import Decimal

import httpx

BASE = "https://sicbo-production.up.railway.app"
TIMEOUT = 15


def section(name: str) -> None:
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")


def check(label: str, ok: bool, detail: str = "") -> bool:
    icon = "OK  " if ok else "FAIL"
    line = f"  [{icon}] {label}"
    if detail:
        line += f" - {detail}"
    print(line)
    return ok


def main() -> int:
    passed = 0
    failed = 0

    section("1. INFRASTRUCTURE")
    r = httpx.get(f"{BASE}/health", timeout=TIMEOUT)
    if check("GET /health", r.status_code == 200 and r.json().get("env") == "production"):
        passed += 1
    else:
        failed += 1

    r = httpx.get(f"{BASE}/docs", timeout=TIMEOUT)
    if check("GET /docs (Swagger UI)", r.status_code == 200):
        passed += 1
    else:
        failed += 1

    section("2. AUTH")
    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "SicboAdmin2026"}, timeout=TIMEOUT)
    admin_ok = r.status_code == 200
    if check("POST /api/auth/login (admin)", admin_ok):
        passed += 1
        admin_token = r.json()["tokens"]["access_token"]
        admin_id = r.json()["user"]["id"]
        AH = {"Authorization": f"Bearer {admin_token}"}
    else:
        failed += 1
        return 1

    r = httpx.get(f"{BASE}/api/auth/me", headers=AH, timeout=TIMEOUT)
    if check("GET /api/auth/me (admin)", r.status_code == 200 and r.json()["username"] == "admin"):
        passed += 1
    else:
        failed += 1

    r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "wrong"}, timeout=TIMEOUT)
    if check("POST /api/auth/login (wrong password) returns 401", r.status_code == 401):
        passed += 1
    else:
        failed += 1

    test_user_name = f"e2e_user_{int(time.time())}"
    r = httpx.post(
        f"{BASE}/api/auth/register",
        json={"username": test_user_name, "password": "testpw12345"},
        timeout=TIMEOUT,
    )
    if check(f"POST /api/auth/register (new user '{test_user_name}')", r.status_code in (200, 201)):
        passed += 1
    else:
        failed += 1
        print("    -> body:", r.text[:200])

    r = httpx.post(
        f"{BASE}/api/auth/login",
        json={"username": test_user_name, "password": "testpw12345"},
        timeout=TIMEOUT,
    )
    user_ok = r.status_code == 200
    if check("POST /api/auth/login (new user)", user_ok):
        passed += 1
        user_token = r.json()["tokens"]["access_token"]
        user_id = r.json()["user"]["id"]
        UH = {"Authorization": f"Bearer {user_token}"}
    else:
        failed += 1
        return 1

    section("3. GAMES & RESULTS")
    r = httpx.get(f"{BASE}/api/games", timeout=TIMEOUT)
    games = r.json() if r.status_code == 200 else []
    if check("GET /api/games (has XSMB with 4 bet types)", any(g["game_id"] == "xsmb" and len(g["bet_types"]) >= 4 for g in games)):
        passed += 1
    else:
        failed += 1

    r = httpx.get(f"{BASE}/api/games/xsmb/cutoff-status", timeout=TIMEOUT)
    if check("GET /api/games/xsmb/cutoff-status", r.status_code == 200 and "is_open" in r.json()):
        passed += 1
    else:
        failed += 1

    r = httpx.get(f"{BASE}/api/results/xsmb", params={"limit": 7}, timeout=TIMEOUT)
    if check("GET /api/results/xsmb (history)", r.status_code == 200):
        passed += 1
    else:
        failed += 1

    section("4. WALLET — USER FLOW")
    r = httpx.get(f"{BASE}/api/wallet/balance", headers=UH, timeout=TIMEOUT)
    if check("GET /api/wallet/balance (new user = 0)", r.status_code == 200 and Decimal(r.json()["balance"]) == 0):
        passed += 1
    else:
        failed += 1

    r = httpx.post(
        f"{BASE}/api/wallet/deposit/init",
        headers=UH,
        json={"amount": 100000, "payment_method": "bank_transfer"},
        timeout=TIMEOUT,
    )
    deposit_ok = r.status_code == 201
    if check("POST /api/wallet/deposit/init (100k)", deposit_ok):
        passed += 1
        deposit = r.json()
        deposit_id = deposit["deposit_id"]
        transfer_content = deposit["transfer_content"]
        if check("  deposit has NAP code + QR + bank account", bool(deposit.get("qr_url") and deposit.get("bank_account") and transfer_content.startswith("NAP"))):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1
        return 1

    section("5. WALLET — ADMIN CONFIRM DEPOSIT")
    r = httpx.get(f"{BASE}/api/admin/deposits/pending", headers=AH, timeout=TIMEOUT)
    pending_has_new = r.status_code == 200 and any(d["id"] == deposit_id for d in r.json()["items"])
    if check("GET /api/admin/deposits/pending shows new deposit", pending_has_new):
        passed += 1
    else:
        failed += 1

    r = httpx.post(
        f"{BASE}/api/admin/deposits/{deposit_id}/confirm",
        headers=AH,
        json={"note": "e2e test confirm"},
        timeout=TIMEOUT,
    )
    if check(f"POST /api/admin/deposits/{deposit_id}/confirm", r.status_code == 200 and r.json()["status"] == "confirmed"):
        passed += 1
    else:
        failed += 1
        print("    body:", r.text[:200])

    r = httpx.post(
        f"{BASE}/api/admin/deposits/{deposit_id}/confirm",
        headers=AH,
        json={"note": "retry"},
        timeout=TIMEOUT,
    )
    if check("POST confirm AGAIN returns 409 (idempotency)", r.status_code == 409):
        passed += 1
    else:
        failed += 1

    r = httpx.get(f"{BASE}/api/wallet/balance", headers=UH, timeout=TIMEOUT)
    balance = Decimal(r.json()["balance"]) if r.status_code == 200 else Decimal(0)
    if check(f"GET /api/wallet/balance after confirm (= 100000)", balance == 100000):
        passed += 1
    else:
        failed += 1
        print(f"    actual: {balance}")

    section("6. ADMIN — DIRECT CREDIT")
    r = httpx.post(
        f"{BASE}/api/admin/deposits/credit",
        headers=AH,
        json={"user_id": user_id, "amount": 50000, "note": "welcome bonus"},
        timeout=TIMEOUT,
    )
    if check("POST /api/admin/deposits/credit (+50k bonus)", r.status_code == 200):
        passed += 1
    else:
        failed += 1
        print("    body:", r.text[:200])

    r = httpx.get(f"{BASE}/api/wallet/balance", headers=UH, timeout=TIMEOUT)
    if check("Balance after bonus = 150000", Decimal(r.json()["balance"]) == 150000):
        passed += 1
    else:
        failed += 1

    section("7. BETTING")
    r = httpx.get(f"{BASE}/api/games/xsmb/cutoff-status", timeout=TIMEOUT)
    is_open = r.json().get("is_open", False) if r.status_code == 200 else False
    if not is_open:
        check("Cutoff closed (after 18:10) — skip place bet tests", True, "Skipped, will resume after 18:30")
    else:
        r = httpx.post(
            f"{BASE}/api/bets",
            headers=UH,
            json={
                "game_id": "xsmb",
                "bet_type_id": "de",
                "numbers": ["23"],
                "stake_per_point": 1000,
                "points": 1,
            },
            timeout=TIMEOUT,
        )
        if check("POST /api/bets (Đề số 23, 1k)", r.status_code in (200, 201)):
            passed += 1
            bet_id = r.json().get("id")
        else:
            failed += 1
            print("    body:", r.text[:200])
            bet_id = None

        r = httpx.get(f"{BASE}/api/bets", headers=UH, params={"limit": 5}, timeout=TIMEOUT)
        if check("GET /api/bets (has the bet)", r.status_code == 200 and any(b.get("id") == bet_id for b in r.json().get("items", []))):
            passed += 1
        else:
            failed += 1

        # Cancel bet (if cutoff still open)
        if bet_id:
            r = httpx.delete(f"{BASE}/api/bets/{bet_id}", headers=UH, timeout=TIMEOUT)
            if check(f"DELETE /api/bets/{bet_id} (cancel)", r.status_code == 200):
                passed += 1
            else:
                failed += 1

    section("8. WITHDRAWAL FLOW")
    r = httpx.post(
        f"{BASE}/api/wallet/withdraw",
        headers=UH,
        json={
            "amount": 50000,
            "payment_method": "bank_transfer",
            "account_number": "1234567890",
            "account_name": "TEST USER",
            "bank_name": "BIDV",
        },
        timeout=TIMEOUT,
    )
    if check("POST /api/wallet/withdraw (50k)", r.status_code in (200, 201)):
        passed += 1
        withdrawal = r.json()
        withdrawal_id = withdrawal["id"]
    else:
        failed += 1
        print("    body:", r.text[:200])
        withdrawal_id = None

    r = httpx.get(f"{BASE}/api/wallet/balance", headers=UH, timeout=TIMEOUT)
    if check("Balance after withdrawal request (-50k held)", Decimal(r.json()["balance"]) <= 100000):
        passed += 1
    else:
        failed += 1

    if withdrawal_id:
        r = httpx.get(f"{BASE}/api/admin/withdrawals/pending", headers=AH, timeout=TIMEOUT)
        if check("Admin sees pending withdrawal", r.status_code == 200 and any(w["id"] == withdrawal_id for w in r.json()["items"])):
            passed += 1
        else:
            failed += 1

        # Reject (to return money) — keep balance for follow-up testing
        r = httpx.post(
            f"{BASE}/api/admin/withdrawals/{withdrawal_id}/reject",
            headers=AH,
            json={"reason": "e2e test reject"},
            timeout=TIMEOUT,
        )
        if check("POST /api/admin/withdrawals/{id}/reject (refund user)", r.status_code == 200):
            passed += 1
        else:
            failed += 1

    section("9. TRANSACTION HISTORY")
    r = httpx.get(f"{BASE}/api/wallet/transactions", headers=UH, timeout=TIMEOUT)
    if check("GET /api/wallet/transactions (>= 3 txs)", r.status_code == 200 and len(r.json()["items"]) >= 3):
        passed += 1
    else:
        failed += 1

    section("10. ADMIN STATS & USERS")
    r = httpx.get(f"{BASE}/api/admin/stats", headers=AH, timeout=TIMEOUT)
    if check("GET /api/admin/stats", r.status_code == 200 and "total_users" in r.json()):
        passed += 1
    else:
        failed += 1

    r = httpx.get(f"{BASE}/api/admin/users", headers=AH, params={"search": test_user_name}, timeout=TIMEOUT)
    if check(f"GET /api/admin/users search='{test_user_name}'", r.status_code == 200 and len(r.json()["items"]) >= 1):
        passed += 1
    else:
        failed += 1

    section("11. WEBHOOKS")
    r = httpx.post(f"{BASE}/api/webhooks/sepay", headers={"Authorization": "Apikey wrong"}, json={}, timeout=TIMEOUT)
    if check("POST /api/webhooks/sepay (wrong key) returns 401", r.status_code == 401):
        passed += 1
    else:
        failed += 1

    section("12. TELEGRAM BOT INFRA")
    r = httpx.get(
        "https://api.telegram.org/bot8949889605:AAEtrOVzCukEVOKTeD_r0qoxMXg9uGaFbW8/getWebhookInfo",
        timeout=TIMEOUT,
    )
    wh_url = r.json().get("result", {}).get("url", "")
    if check(
        "Telegram webhook registered with Sicbo",
        wh_url == f"{BASE}/api/telegram/webhook",
        f"url={wh_url}",
    ):
        passed += 1
    else:
        failed += 1

    section(f"RESULT: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

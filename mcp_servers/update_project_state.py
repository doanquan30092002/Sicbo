#!/usr/bin/env python3
"""Auto-updates project-state.md by scanning actual codebase state."""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND = PROJECT_ROOT / "backend" / "app"
STATE_FILE = PROJECT_ROOT / ".claude" / "agent-memory" / "project-state.md"


def has_content(path: Path, min_lines: int = 5) -> bool:
    if not path.exists():
        return False
    lines = [
        l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if l.strip() and not l.strip().startswith("#") and l.strip() not in ("pass", "...")
    ]
    return len(lines) >= min_lines


def check_domain() -> dict:
    d = BACKEND / "domain"
    return {
        "entities/user.py": has_content(d / "entities" / "user.py"),
        "entities/bet.py": has_content(d / "entities" / "bet.py"),
        "entities/wallet.py": has_content(d / "entities" / "wallet.py"),
        "entities/game_result.py": has_content(d / "entities" / "game_result.py"),
        "repositories/ (interfaces)": (d / "repositories").exists() and any((d / "repositories").iterdir()),
        "games/base.py (AbstractGame)": has_content(d / "games" / "base.py"),
        "games/registry.py": has_content(d / "games" / "registry.py"),
        "games/xsmb/game.py": has_content(d / "games" / "xsmb" / "game.py"),
    }


def check_application() -> dict:
    uc = BACKEND / "application" / "use_cases"
    return {
        "RegisterUser": has_content(uc / "auth" / "register_user.py"),
        "LoginUser": has_content(uc / "auth" / "login_user.py"),
        "PlaceBet": has_content(uc / "betting" / "place_bet.py"),
        "CancelBet": has_content(uc / "betting" / "cancel_bet.py"),
        "SettleBets": has_content(uc / "betting" / "settle_bets.py"),
        "FetchAndStoreResult": has_content(uc / "lottery" / "fetch_and_store_result.py"),
        "RequestDeposit": has_content(uc / "wallet" / "request_deposit.py"),
        "ConfirmDeposit": has_content(uc / "wallet" / "confirm_deposit.py"),
        "RequestWithdrawal": has_content(uc / "wallet" / "request_withdrawal.py"),
        "ProcessWithdrawal": has_content(uc / "admin" / "process_withdrawal.py"),
    }


def check_infrastructure() -> dict:
    infra = BACKEND / "infrastructure"
    repos = infra / "database" / "repositories"
    models_dir = infra / "database" / "models"
    utils = BACKEND / "utils"
    return {
        "ORM models (SQLAlchemy)": models_dir.exists() and has_content(models_dir / "user_model.py"),
        "security.py (JWT + bcrypt)": has_content(utils / "security.py"),
        "UserRepository (concrete)": has_content(repos / "pg_user_repo.py"),
        "BetRepository (concrete)": has_content(repos / "pg_bet_repo.py"),
        "WalletRepository (concrete)": has_content(repos / "pg_wallet_repo.py"),
        "GameResultRepository (concrete)": has_content(repos / "pg_game_result_repo.py"),
        "XSMB API fetcher": has_content(infra / "external" / "xsmb_fetcher.py"),
        "SePay gateway": has_content(infra / "external" / "sepay_gateway.py"),
        "Telegram notifier": has_content(infra / "notifications" / "telegram_notifier.py"),
    }


def check_interfaces() -> dict:
    iface = BACKEND / "interfaces"
    routers = iface / "api" / "routers"
    return {
        "FastAPI main.py": has_content(iface / "api" / "main.py"),
        "auth router": has_content(routers / "auth.py"),
        "bets router": has_content(routers / "bets.py"),
        "wallet router": has_content(routers / "wallet.py"),
        "admin router": has_content(routers / "admin.py"),
        "webhook router": has_content(routers / "webhooks.py"),
        "Telegram bot handlers": has_content(iface / "telegram_bot" / "bot.py"),
        "APScheduler jobs": has_content(iface / "scheduler" / "jobs.py"),
    }


def check_frontend() -> dict:
    fe = PROJECT_ROOT / "frontend"
    return {
        "frontend/ directory": fe.exists(),
        "package.json": (fe / "package.json").exists(),
        "src/ directory": (fe / "src").exists(),
        "app/ router": (fe / "src" / "app").exists(),
    }


def check_migrations() -> dict:
    versions = PROJECT_ROOT / "backend" / "migrations" / "versions"
    if not versions.exists():
        return {"has_migrations": False, "count": 0}
    files = [f for f in versions.iterdir() if f.suffix == ".py" and f.name != "__init__.py"]
    return {"has_migrations": len(files) > 0, "count": len(files)}


def determine_phase(domain, app, infra, iface, fe, migrations) -> str:
    domain_done = all(domain.values())
    app_done = all(app.values())
    infra_done = all(infra.values())
    api_running = iface.get("FastAPI main.py") and iface.get("auth router")
    fe_done = fe.get("src/ directory")

    if not domain_done:
        return "Phase 1 — Foundation (đang làm)"
    if not app_done:
        return "Phase 2 — Application Use Cases (đang làm)"
    if not migrations["has_migrations"]:
        return "Phase 3 — Infrastructure + Migrations (đang làm)"
    if not infra_done:
        return "Phase 3 — Infrastructure (đang làm)"
    if not api_running:
        return "Phase 4 — API Layer (đang làm)"
    if not fe_done:
        return "Phase 5 — Frontend Next.js (đang làm)"
    return "Phase 6 — Integration, Testing & Deploy"


def icon(val: bool) -> str:
    return "✅" if val else "❌"


def section(title: str, checks: dict) -> str:
    done = sum(checks.values())
    total = len(checks)
    lines = [f"## {title} ({done}/{total})"]
    for k, v in checks.items():
        lines.append(f"- {icon(v)} {k}")
    return "\n".join(lines)


def main():
    domain = check_domain()
    app = check_application()
    infra = check_infrastructure()
    iface = check_interfaces()
    fe = check_frontend()
    migrations = check_migrations()

    phase = determine_phase(domain, app, infra, iface, fe, migrations)
    today = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""---
name: project-state
description: Trạng thái hiện tại của dự án Sicbo - phase đang làm, những gì đã xong
type: project
---

# Trạng thái Dự án Sicbo

**Ngày cập nhật:** {today} *(auto-updated bởi Stop hook)*

## Phase hiện tại: {phase}

{section("Domain Layer", domain)}

{section("Application Layer (Use Cases)", app)}

{section("Infrastructure Layer", infra)}

## Alembic Migrations
- {icon(migrations["has_migrations"])} Migration files ({migrations["count"]} files trong versions/)

{section("Interfaces Layer (API + Bot + Scheduler)", iface)}

{section("Frontend (Next.js 14)", fe)}

## Quyết định kiến trúc quan trọng
- Cutoff time: **18:10** (server-side, không tin client)
- `all_last2` cho Lô: **LIST có duplicate** (không phải set)
- Single process Railway: FastAPI + APScheduler + Telegram Bot cùng chạy
- Scheduler tự đăng ký jobs từ `GameRegistry.all_active()`
"""

    STATE_FILE.write_text(content, encoding="utf-8")
    sys.stdout.buffer.write(f"project-state.md updated\n".encode("utf-8"))
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"update_project_state: {e}", file=sys.stderr)
        sys.exit(0)  # don't block Claude from stopping

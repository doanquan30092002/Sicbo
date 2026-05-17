---
name: project-state
description: Trạng thái hiện tại của dự án Sicbo - phase đang làm, những gì đã xong
type: project
---

# Trạng thái Dự án Sicbo

**Ngày cập nhật:** 2026-05-17 09:23 *(auto-updated bởi Stop hook)*

## Phase hiện tại: Phase 3 — Infrastructure (đang làm)

## Domain Layer (8/8)
- ✅ entities/user.py
- ✅ entities/bet.py
- ✅ entities/wallet.py
- ✅ entities/game_result.py
- ✅ repositories/ (interfaces)
- ✅ games/base.py (AbstractGame)
- ✅ games/registry.py
- ✅ games/xsmb/game.py

## Application Layer (Use Cases) (10/10)
- ✅ RegisterUser
- ✅ LoginUser
- ✅ PlaceBet
- ✅ CancelBet
- ✅ SettleBets
- ✅ FetchAndStoreResult
- ✅ RequestDeposit
- ✅ ConfirmDeposit
- ✅ RequestWithdrawal
- ✅ ProcessWithdrawal

## Infrastructure Layer (5/9)
- ✅ ORM models (SQLAlchemy)
- ✅ security.py (JWT + bcrypt)
- ❌ UserRepository (concrete)
- ❌ BetRepository (concrete)
- ❌ WalletRepository (concrete)
- ❌ GameResultRepository (concrete)
- ✅ XSMB API fetcher
- ✅ SePay gateway
- ✅ Telegram notifier

## Alembic Migrations
- ✅ Migration files (1 files trong versions/)

## Interfaces Layer (API + Bot + Scheduler) (8/8)
- ✅ FastAPI main.py
- ✅ auth router
- ✅ bets router
- ✅ wallet router
- ✅ admin router
- ✅ webhook router
- ✅ Telegram bot handlers
- ✅ APScheduler jobs

## Frontend (Next.js 14) (2/4)
- ✅ frontend/ directory
- ✅ package.json
- ❌ src/ directory
- ❌ app/ router

## Quyết định kiến trúc quan trọng
- Cutoff time: **18:10** (server-side, không tin client)
- `all_last2` cho Lô: **LIST có duplicate** (không phải set)
- Single process Railway: FastAPI + APScheduler + Telegram Bot cùng chạy
- Scheduler tự đăng ký jobs từ `GameRegistry.all_active()`

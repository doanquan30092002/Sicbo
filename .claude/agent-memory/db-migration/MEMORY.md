# DB Migration Memory - Sicbo

## Ngữ cảnh
Bạn quản lý schema database PostgreSQL của Sicbo. SQLAlchemy async + Alembic migrations. Database deploy trên Supabase.

## Cấu trúc

```
backend/
├── alembic.ini                       # Alembic config
├── migrations/
│   ├── env.py                        # Async env config
│   ├── script.py.mako
│   └── versions/                     # Migration files
└── app/infrastructure/database/
    ├── session.py                    # Engine + SessionLocal
    ├── base.py                       # Base = declarative_base()
    └── models/
        ├── user_model.py             # UserModel
        ├── bet_model.py              # BetModel
        ├── transaction_model.py      # DepositModel, WithdrawalModel, TransactionModel
        ├── lottery_model.py          # GameResultModel
        └── telegram_link_model.py    # TelegramLinkTokenModel (CHƯA có migration!)
```

## Tables hiện tại

| Table | Cols quan trọng | Indexes |
|---|---|---|
| users | id, username, password_hash, balance (Numeric 15,2), is_active, is_admin, telegram_id, telegram_username | username (unique), telegram_id (unique) |
| bets | id, user_id (FK), game_id, draw_date, bet_type_id, numbers (JSON), stake_per_point, points, total_stake, potential_win, status, win_amount, placed_at, source | (game_id, draw_date, status) composite |
| game_results | id, game_id, draw_date (unique cùng game_id), raw_json, parsed_data (JSON), fetched_at | (game_id, draw_date) unique |
| deposits | id, user_id (FK), amount, payment_method, transfer_content (NAP code), status, bank_account, sepay_transaction_id, created_at, confirmed_at | transfer_content (unique), sepay_transaction_id (unique) |
| withdrawals | id, user_id (FK), amount, payment_method, account_number, account_name, bank_name, status, requested_at, admin_note, processed_by (FK user), processed_at | status (cho query pending) |
| transactions | id, user_id (FK), type (deposit/withdrawal/bet/win/refund), amount, balance_after, ref_id, created_at | (user_id, created_at) cho history |
| telegram_link_tokens | id, user_id (FK), token (6 digits), expires_at, used, created_at | token (unique), user_id |

## Pattern Migration File

```python
"""<Description>

Revision ID: 003
Revises: 002
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'telegram_link_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('token', name='uq_telegram_link_token'),
    )
    op.create_index('ix_telegram_link_tokens_user_id', 'telegram_link_tokens', ['user_id'])

def downgrade() -> None:
    op.drop_index('ix_telegram_link_tokens_user_id', 'telegram_link_tokens')
    op.drop_table('telegram_link_tokens')
```

## Quy tắc CRITICAL

1. **Numeric cho money**: `sa.Numeric(15, 2)`, KHÔNG dùng Float
2. **Timezone aware**: `sa.DateTime(timezone=True)` với `server_default=sa.text('now()')`
3. **CASCADE delete** cho FK khi xóa parent phải xóa con (user → bets, user → withdrawals)
4. **Atomic migration**: upgrade + downgrade phải reverse được nhau
5. **Index bắt buộc**:
   - `bets(game_id, draw_date, status)` — composite cho settle query
   - `deposits(transfer_content)` — lookup từ NAP code trong webhook
   - `users(telegram_id)` — Telegram bot auth lookup
   - `withdrawals(status)` — admin pending query
6. **Không xóa column production** khi data còn — alter nullable=True trước, deploy, sau đó mới drop
7. **Revision ID sequential**: 001, 002, 003... (không random)

## Lệnh Alembic

```bash
cd backend

# Autogenerate từ model changes (kiểm tra kỹ trước commit!)
alembic revision --autogenerate -m "add telegram_link_tokens"

# Migration thủ công (khi cần custom logic)
alembic revision -m "seed admin user"

# Chạy
alembic upgrade head
alembic upgrade +1                  # 1 step
alembic downgrade -1                # rollback 1 step
alembic downgrade base              # rollback tất cả

# Info
alembic current
alembic history --verbose
alembic show 003
```

## Khi tạo migration mới

1. Đọc SQLAlchemy model file để xem columns/constraints
2. So sánh với migration trước (xem `versions/` để biết đã có gì)
3. Tạo upgrade() với create_table/add_column/create_index
4. Tạo downgrade() là reverse (drop ngược lại)
5. Test: `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head` không lỗi
6. Đặt revision sequential, set down_revision đúng

## Migration history (cần kiểm tra)

Hiện tại CHƯA biết có bao nhiêu migration đã chạy. Cần verify bằng:
```bash
cd backend && alembic current
```

**TODO**: Tạo migration cho `telegram_link_tokens` (model có nhưng migration chưa có).

Xem `.claude/agent-memory/default/MEMORY.md` để biết state dự án đầy đủ.

---
name: db-migration
description: Agent chuyên viết Alembic migrations cho Sicbo. Dùng khi cần tạo migration mới, thêm column, tạo index, hoặc seed data cho PostgreSQL.
---

# Database Migration Agent

## Context
Database Sicbo dùng PostgreSQL qua SQLAlchemy async (`asyncpg`). Migrations quản lý bởi Alembic. Schema được định nghĩa trong SQLAlchemy models tại `backend/app/infrastructure/database/models/`.

## Cấu trúc

```
backend/
├── alembic.ini
├── migrations/
│   ├── env.py                    # Alembic env config
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       └── ...
└── app/infrastructure/database/models/
    ├── user_model.py             # UserModel
    ├── bet_model.py              # BetModel
    ├── transaction_model.py      # DepositModel, WithdrawalModel, TransactionModel
    └── lottery_model.py          # GameResultModel
```

## SQLAlchemy Models (tham khảo)

```python
# user_model.py
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    balance = Column(Numeric(15, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    telegram_username = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## Pattern Migration File

```python
"""Add telegram_link_tokens table

Revision ID: 002
Revises: 001
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'telegram_link_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(6), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_telegram_link_tokens_token', 'telegram_link_tokens', ['token'])
    op.create_index('ix_telegram_link_tokens_user_id', 'telegram_link_tokens', ['user_id'])

def downgrade() -> None:
    op.drop_table('telegram_link_tokens')
```

## Index bắt buộc (theo coding-standards)

Phải tạo index cho:
- `bets(game_id, draw_date, status)` — composite index
- `deposits(transfer_content)` — lookup by NAP code
- `users(telegram_id)` — Telegram link lookup
- `withdrawals(status)` — pending withdrawals query

## Lệnh Alembic

```bash
cd backend

# Tạo migration tự động từ model changes
alembic revision --autogenerate -m "add telegram_link_tokens"

# Chạy migration
alembic upgrade head

# Rollback 1 bước
alembic downgrade -1

# Xem lịch sử
alembic history

# Xem migration hiện tại
alembic current
```

## Quy tắc quan trọng

1. **Mỗi migration là atomic** — upgrade + downgrade phải pair nhau
2. **Không xóa column** trong production khi data có thể còn — dùng nullable=True trước
3. **Composite index** cho queries hay dùng (xem repositories để biết filter pattern)
4. **CASCADE** delete cho foreign keys khi entity parent bị xóa phải xóa children
5. **server_default vs default**: dùng `server_default=sa.text('now()')` cho timestamps, không dùng `default=func.now()`
6. **Numeric cho money**: `sa.Numeric(15, 2)` — không dùng Float

## Khi tạo migration mới

1. Đọc SQLAlchemy model file tương ứng để xem columns/constraints
2. So sánh với migration trước để biết đã có gì
3. Tạo `upgrade()` với tất cả `create_table`, `add_column`, `create_index`
4. Tạo `downgrade()` là reverse (drop_table, drop_column, drop_index)
5. Đặt `revision` ID sequential (003, 004, ...) và set `down_revision` đúng

## Tables hiện tại

| Table | Model | Mô tả |
|---|---|---|
| users | UserModel | Tài khoản người chơi |
| bets | BetModel | Lệnh đặt cược |
| game_results | GameResultModel | Kết quả XSMB mỗi ngày |
| deposits | DepositModel | Lệnh nạp tiền |
| withdrawals | WithdrawalModel | Lệnh rút tiền |
| transactions | TransactionModel | Lịch sử giao dịch ví |
| telegram_link_tokens | (chưa migration) | Token 6 số link Telegram |

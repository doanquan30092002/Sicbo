# Skill: Database Migrations - Sicbo

## Workflow tạo migration

### 1. Thay đổi SQLAlchemy model
Sửa file trong `backend/app/infrastructure/database/models/` (ví dụ thêm column mới)

### 2. Generate migration (auto)
```bash
cd backend
alembic revision --autogenerate -m "add <description>"
```

### 3. Xem migration đã generate
```bash
# File mới ở migrations/versions/<id>_<description>.py
# CHECK kỹ trước khi commit — autogenerate có thể sai/thiếu:
# - Index composite
# - Server defaults
# - Custom constraints
```

### 4. Test migration locally
```bash
alembic upgrade head      # Apply
alembic downgrade -1      # Rollback
alembic upgrade head      # Reapply — phải không lỗi
```

### 5. Verify schema
```bash
# Connect DB và check
psql $DATABASE_URL -c "\d+ <table_name>"
```

## Lệnh hay dùng

```bash
# Trạng thái hiện tại
alembic current
alembic history --verbose

# Apply/rollback
alembic upgrade head           # Latest
alembic upgrade +1             # Forward 1 step
alembic upgrade <revision_id>  # Specific revision
alembic downgrade -1           # Back 1 step
alembic downgrade base         # Rollback tất cả

# Inspect
alembic show <revision_id>     # Xem migration content

# Manual migration (no autogenerate)
alembic revision -m "seed admin user"
```

## Template migration

```python
"""<description>

Revision ID: 003
Revises: 002
Create Date: 2026-05-16 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Thêm column
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    
    # Thêm table
    op.create_table(
        'telegram_link_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(6), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('token', name='uq_telegram_link_tokens_token'),
    )
    
    # Index composite
    op.create_index('ix_bets_game_date_status', 'bets', ['game_id', 'draw_date', 'status'])


def downgrade() -> None:
    op.drop_index('ix_bets_game_date_status', table_name='bets')
    op.drop_table('telegram_link_tokens')
    op.drop_column('users', 'phone')
```

## Quy tắc CRITICAL

1. **Numeric cho money**: `sa.Numeric(15, 2)` (KHÔNG Float)
2. **Timestamp**: `sa.DateTime(timezone=True)` + `server_default=sa.text('now()')`
3. **CASCADE**: FK relationships parent→child phải có `ondelete='CASCADE'` nếu xóa parent xóa child
4. **Upgrade + Downgrade**: Phải reverse được nhau
5. **Index trước query**: Mọi query repository hay dùng phải có index tương ứng
6. **Không drop column production**: nullable=True trước, deploy, sau đó mới drop ở migration sau
7. **Sequential revision**: 001, 002, 003... (không random ID)

## Index bắt buộc

```python
# Composite cho settle query
op.create_index('ix_bets_game_date_status', 'bets', ['game_id', 'draw_date', 'status'])

# Lookup nhanh từ webhook
op.create_index('ix_deposits_transfer_content', 'deposits', ['transfer_content'], unique=True)

# Telegram bot auth
op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

# Admin pending query
op.create_index('ix_withdrawals_status', 'withdrawals', ['status'])
```

## Migration production (Supabase)

```bash
# 1. Đặt DATABASE_URL=postgresql+asyncpg://...supabase...
# 2. Backup trước (Supabase Dashboard → Database → Backups)
# 3. Run migration
alembic upgrade head

# 4. Verify
psql $DATABASE_URL -c "SELECT version_num FROM alembic_version;"
```

## Troubleshooting

| Lỗi | Giải pháp |
|---|---|
| `Target database is not up to date` | `alembic upgrade head` trước khi tạo migration mới |
| `Can't locate revision` | Check `down_revision` đúng ID prev migration không |
| Autogenerate empty | Model chưa import vào `migrations/env.py` |
| `relation already exists` | Database có schema thừa, drop manual hoặc dùng `IF NOT EXISTS` |

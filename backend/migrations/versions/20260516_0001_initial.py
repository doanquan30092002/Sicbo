"""initial schema — users, bets, transactions, deposits, withdrawals, game_results, telegram_link_tokens

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("balance", sa.Numeric(15, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phone", sa.String(15), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_username", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    # game_results
    op.create_table(
        "game_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.String(20), nullable=False),
        sa.Column("draw_date", sa.Date(), nullable=False),
        sa.Column("parsed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("game_id", "draw_date", name="uq_game_result_date"),
    )
    op.create_index("ix_game_results_game_id", "game_results", ["game_id"])
    op.create_index("ix_game_results_draw_date", "game_results", ["draw_date"])

    # bets
    op.create_table(
        "bets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("game_id", sa.String(20), nullable=False),
        sa.Column("draw_date", sa.Date(), nullable=False),
        sa.Column("bet_type_id", sa.String(20), nullable=False),
        sa.Column("numbers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("stake_per_point", sa.Numeric(10, 2), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_stake", sa.Numeric(10, 2), nullable=False),
        sa.Column("potential_win", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("win_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("source", sa.String(20), nullable=False, server_default="web"),
        sa.Column("placed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_bets_game_date_status", "bets", ["game_id", "draw_date", "status"])
    op.create_index("ix_bets_user_date", "bets", ["user_id", "draw_date"])

    # transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("balance_before", sa.Numeric(15, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(15, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("related_bet_id", sa.Integer(), sa.ForeignKey("bets.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])

    # deposits
    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("transfer_content", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("bank_account", sa.String(50), nullable=True),
        sa.Column("sepay_transaction_id", sa.String(100), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("transfer_content", name="uq_deposits_transfer_content"),
        sa.UniqueConstraint("sepay_transaction_id", name="uq_deposits_sepay_tx"),
    )
    op.create_index("ix_deposits_user_id", "deposits", ["user_id"])
    op.create_index("ix_deposits_transfer_content", "deposits", ["transfer_content"])

    # withdrawals
    op.create_table(
        "withdrawals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("account_number", sa.String(50), nullable=False),
        sa.Column("account_name", sa.String(100), nullable=False),
        sa.Column("bank_name", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("processed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_withdrawals_user_id", "withdrawals", ["user_id"])
    op.create_index("ix_withdrawals_status", "withdrawals", ["status"])

    # telegram_link_tokens
    op.create_table(
        "telegram_link_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_telegram_link_tokens_token"),
    )
    op.create_index("ix_telegram_link_tokens_user_id", "telegram_link_tokens", ["user_id"])
    op.create_index("ix_telegram_link_tokens_token", "telegram_link_tokens", ["token"])


def downgrade() -> None:
    op.drop_index("ix_telegram_link_tokens_token", table_name="telegram_link_tokens")
    op.drop_index("ix_telegram_link_tokens_user_id", table_name="telegram_link_tokens")
    op.drop_table("telegram_link_tokens")

    op.drop_index("ix_withdrawals_status", table_name="withdrawals")
    op.drop_index("ix_withdrawals_user_id", table_name="withdrawals")
    op.drop_table("withdrawals")

    op.drop_index("ix_deposits_transfer_content", table_name="deposits")
    op.drop_index("ix_deposits_user_id", table_name="deposits")
    op.drop_table("deposits")

    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("ix_bets_user_date", table_name="bets")
    op.drop_index("ix_bets_game_date_status", table_name="bets")
    op.drop_table("bets")

    op.drop_index("ix_game_results_draw_date", table_name="game_results")
    op.drop_index("ix_game_results_game_id", table_name="game_results")
    op.drop_table("game_results")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")

"""create subscriptions and payments

Revision ID: c3b1a9d4e621
Revises: 8ca2d773dfb1
"""

import sqlalchemy as sa
from alembic import op

revision = "c3b1a9d4e621"
down_revision = "8ca2d773dfb1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("custom_interval_days", sa.Integer(), nullable=True),
        sa.Column("billing_day", sa.Integer(), nullable=False),
        sa.Column("next_payment_date", sa.Date(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_subscriptions_amount_positive"),
        sa.CheckConstraint(
            "billing_day >= 1 AND billing_day <= 31", name="ck_subscriptions_billing_day"
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_subscriptions_user_next_payment", "subscriptions", ["user_id", "next_payment_date"]
    )
    op.create_table(
        "subscription_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("expense_id", sa.Integer(), nullable=False),
        sa.Column("client_operation_id", sa.Uuid(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount > 0", name="ck_subscription_payments_amount_positive"),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expense_id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint(
            "subscription_id", "client_operation_id", name="uq_subscription_payment_operation"
        ),
    )


def downgrade():
    op.drop_table("subscription_payments")
    op.drop_index("ix_subscriptions_user_next_payment", table_name="subscriptions")
    op.drop_table("subscriptions")

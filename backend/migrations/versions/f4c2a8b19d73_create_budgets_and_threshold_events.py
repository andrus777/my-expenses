"""create budgets and threshold events

Revision ID: f4c2a8b19d73
Revises: d8e2f5a71b90
"""

import sqlalchemy as sa
from alembic import op

revision = "f4c2a8b19d73"
down_revision = "d8e2f5a71b90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        sa.CheckConstraint("end_date >= start_date", name="ck_budgets_dates"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint(
            "user_id",
            "category_id",
            "start_date",
            "end_date",
            name="uq_budgets_user_category_period",
        ),
    )
    op.create_index("ix_budgets_user_period", "budgets", ["user_id", "start_date", "end_date"])
    op.create_table(
        "budget_threshold_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.Uuid(), nullable=False),
        sa.Column("budget_id", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("threshold IN (80, 100)", name="ck_budget_events_threshold"),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("budget_id", "threshold", name="uq_budget_events_budget_threshold"),
    )


def downgrade():
    op.drop_table("budget_threshold_events")
    op.drop_index("ix_budgets_user_period", table_name="budgets")
    op.drop_table("budgets")

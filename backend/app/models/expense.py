import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        UniqueConstraint(
            "user_id", "client_operation_id", name="uq_expenses_user_client_operation"
        ),
        Index("ix_expenses_user_expense_date", "user_id", "expense_date"),
        Index("ix_expenses_user_category", "user_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="MANUAL")
    client_operation_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="expenses")  # noqa: F821
    category: Mapped["Category"] = relationship(back_populates="expenses")  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "id": str(self.public_id),
            "category_id": str(self.category.public_id),
            "amount": format(self.amount, ".2f"),
            "currency": self.currency,
            "expense_date": self.expense_date.isoformat(),
            "merchant": self.merchant,
            "description": self.description,
            "comment": self.comment,
            "source": self.source,
            "client_operation_id": str(self.client_operation_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

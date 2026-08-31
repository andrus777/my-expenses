import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_subscriptions_amount_positive"),
        CheckConstraint(
            "billing_day >= 1 AND billing_day <= 31", name="ck_subscriptions_billing_day"
        ),
        Index("ix_subscriptions_user_next_payment", "user_id", "next_payment_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(150))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    frequency: Mapped[str] = mapped_column(String(20))
    custom_interval_days: Mapped[int | None] = mapped_column(Integer)
    billing_day: Mapped[int] = mapped_column(Integer)
    next_payment_date: Mapped[date] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="subscriptions")  # noqa: F821
    category: Mapped["Category"] = relationship()  # noqa: F821
    payments: Mapped[list["SubscriptionPayment"]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.public_id),
            "category_id": str(self.category.public_id),
            "name": self.name,
            "amount": format(self.amount, ".2f"),
            "currency": self.currency,
            "frequency": self.frequency,
            "custom_interval_days": self.custom_interval_days,
            "next_payment_date": self.next_payment_date.isoformat(),
            "comment": self.comment,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SubscriptionPayment(db.Model):
    __tablename__ = "subscription_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_subscription_payments_amount_positive"),
        db.UniqueConstraint(
            "subscription_id", "client_operation_id", name="uq_subscription_payment_operation"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, default=uuid.uuid4
    )
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id", ondelete="CASCADE"))
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="RESTRICT"), unique=True
    )
    client_operation_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True))
    payment_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscription: Mapped[Subscription] = relationship(back_populates="payments")
    expense: Mapped["Expense"] = relationship()  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "id": str(self.public_id),
            "subscription_id": str(self.subscription.public_id),
            "expense_id": str(self.expense.public_id),
            "client_operation_id": str(self.client_operation_id),
            "payment_date": self.payment_date.isoformat(),
            "amount": format(self.amount, ".2f"),
            "created_at": self.created_at.isoformat(),
        }

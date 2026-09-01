import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Receipt(db.Model):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    provider_receipt_id: Mapped[str | None] = mapped_column(String(255))
    merchant: Mapped[str] = mapped_column(String(255))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    purchase_date: Mapped[date] = mapped_column(Date)
    finalized_expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("expenses.id", ondelete="RESTRICT"), unique=True
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="receipts")  # noqa: F821
    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan", order_by="ReceiptItem.id"
    )
    finalized_expense: Mapped["Expense | None"] = relationship()  # noqa: F821
    job: Mapped["ReceiptJob"] = relationship(back_populates="receipt", uselist=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.public_id),
            "merchant": self.merchant,
            "total": format(self.total, ".2f"),
            "currency": self.currency,
            "purchase_date": self.purchase_date.isoformat(),
            "items": [item.to_dict() for item in self.items],
            "finalized": self.finalized_expense_id is not None,
            "expense_id": str(self.finalized_expense.public_id) if self.finalized_expense else None,
        }


class ReceiptItem(db.Model):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    receipt: Mapped[Receipt] = relationship(back_populates="items")

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "quantity": format(self.quantity, ".3f"),
            "price": format(self.price, ".2f"),
            "total": format(self.total, ".2f"),
        }


class ReceiptJob(db.Model):
    __tablename__ = "receipt_jobs"
    __table_args__ = (Index("ix_receipt_jobs_user_status", "user_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    receipt_id: Mapped[int | None] = mapped_column(
        ForeignKey("receipts.id", ondelete="SET NULL"), unique=True
    )
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    receipt_data: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(default=0)
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["User"] = relationship()  # noqa: F821
    receipt: Mapped[Receipt | None] = relationship(back_populates="job")

    def to_dict(self) -> dict:
        return {
            "job_id": str(self.public_id),
            "status": self.status,
            "attempts": self.attempts,
            "error": (
                {"code": self.error_code, "message": self.error_message}
                if self.status == "FAILED"
                else None
            ),
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

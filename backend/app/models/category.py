import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name", name="uq_categories_user_normalized_name"),
        Index("ix_categories_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User | None"] = relationship(back_populates="categories")  # noqa: F821
    expenses: Mapped[list["Expense"]] = relationship(back_populates="category")  # noqa: F821

    @property
    def is_system(self) -> bool:
        return self.user_id is None

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "id": str(self.public_id),
            "name": self.name,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

import uuid

from sqlalchemy import or_, select

from app.extensions import db
from app.models import Category


class CategoryRepository:
    def list_visible(self, user_id: int) -> list[Category]:
        statement = (
            select(Category)
            .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
            .order_by(Category.user_id.is_not(None), Category.name)
        )
        return list(db.session.scalars(statement))

    def find_visible(self, public_id: uuid.UUID, user_id: int) -> Category | None:
        statement = select(Category).where(
            Category.public_id == public_id,
            or_(Category.user_id.is_(None), Category.user_id == user_id),
        )
        return db.session.scalar(statement)

    def find_owned(self, public_id: uuid.UUID, user_id: int) -> Category | None:
        return db.session.scalar(
            select(Category).where(Category.public_id == public_id, Category.user_id == user_id)
        )

    def find_by_name(self, name: str, user_id: int) -> Category | None:
        return db.session.scalar(
            select(Category).where(
                Category.normalized_name == name.casefold(), Category.user_id == user_id
            )
        )

    def add(self, category: Category) -> None:
        db.session.add(category)

    def has_expenses(self, category_id: int) -> bool:
        from app.models import Expense

        return (
            db.session.scalar(select(Expense.id).where(Expense.category_id == category_id).limit(1))
            is not None
        )

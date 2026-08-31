import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Category, Expense


@dataclass(frozen=True)
class ExpenseFilters:
    page: int
    per_page: int
    date_from: date | None = None
    date_to: date | None = None
    category_public_id: uuid.UUID | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    currency: str | None = None
    source: str | None = None
    search: str | None = None
    sort: str = "expense_date"
    order: str = "desc"


class ExpenseRepository:
    def find_visible(self, public_id: uuid.UUID, user_id: int) -> Expense | None:
        return db.session.scalar(
            select(Expense)
            .options(joinedload(Expense.category))
            .where(
                Expense.public_id == public_id,
                Expense.user_id == user_id,
                Expense.deleted_at.is_(None),
            )
        )

    def find_by_client_operation(self, operation_id: uuid.UUID, user_id: int) -> Expense | None:
        return db.session.scalar(
            select(Expense)
            .options(joinedload(Expense.category))
            .where(
                Expense.client_operation_id == operation_id,
                Expense.user_id == user_id,
            )
        )

    def list(self, user_id: int, filters: ExpenseFilters) -> tuple[list[Expense], int]:
        statement = (
            select(Expense)
            .join(Expense.category)
            .options(joinedload(Expense.category))
            .where(Expense.user_id == user_id, Expense.deleted_at.is_(None))
        )
        statement = self._apply_filters(statement, filters)
        total = db.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        sort_column = {
            "expense_date": Expense.expense_date,
            "amount": Expense.amount,
            "created_at": Expense.created_at,
        }[filters.sort]
        ordering = asc(sort_column) if filters.order == "asc" else desc(sort_column)
        statement = (
            statement.order_by(ordering, desc(Expense.id))
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
        )
        return list(db.session.scalars(statement).unique()), total

    def add(self, expense: Expense) -> None:
        db.session.add(expense)

    @staticmethod
    def _apply_filters(statement: Select, filters: ExpenseFilters) -> Select:
        if filters.date_from:
            statement = statement.where(Expense.expense_date >= filters.date_from)
        if filters.date_to:
            statement = statement.where(Expense.expense_date <= filters.date_to)
        if filters.category_public_id:
            statement = statement.where(Category.public_id == filters.category_public_id)
        if filters.min_amount is not None:
            statement = statement.where(Expense.amount >= filters.min_amount)
        if filters.max_amount is not None:
            statement = statement.where(Expense.amount <= filters.max_amount)
        if filters.currency:
            statement = statement.where(Expense.currency == filters.currency)
        if filters.source:
            statement = statement.where(Expense.source == filters.source)
        if filters.search:
            statement = statement.where(
                or_(
                    Expense.merchant.icontains(filters.search, autoescape=True),
                    Expense.description.icontains(filters.search, autoescape=True),
                    Expense.comment.icontains(filters.search, autoescape=True),
                )
            )
        return statement

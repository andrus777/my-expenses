import math
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.extensions import db
from app.models import Expense, User
from app.repositories.categories import CategoryRepository
from app.repositories.expenses import ExpenseFilters, ExpenseRepository
from app.schemas.expenses import ExpenseData


class ExpenseService:
    def __init__(self) -> None:
        self.expenses = ExpenseRepository()
        self.categories = CategoryRepository()

    def list(self, user: User, filters: ExpenseFilters) -> tuple[list[Expense], dict[str, int]]:
        expenses, total = self.expenses.list(user.id, filters)
        pages = math.ceil(total / filters.per_page) if total else 0
        return expenses, {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "pages": pages,
        }

    def get(self, public_id: uuid.UUID, user: User) -> Expense:
        expense = self.expenses.find_visible(public_id, user.id)
        if expense is None:
            raise ApiError("EXPENSE_NOT_FOUND", "Расход не найден", 404)
        return expense

    def create(self, data: ExpenseData, user: User) -> tuple[Expense, bool]:
        category = self.categories.find_visible(data.category_public_id, user.id)
        if category is None:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
        existing = self.expenses.find_by_client_operation(data.client_operation_id, user.id)
        if existing is not None:
            self._ensure_equivalent(existing, data, category.id)
            return existing, False

        expense = Expense(
            user_id=user.id,
            category_id=category.id,
            amount=data.amount,
            currency=data.currency,
            expense_date=data.expense_date,
            merchant=data.merchant,
            description=data.description,
            comment=data.comment,
            source=data.source,
            client_operation_id=data.client_operation_id,
        )
        self.expenses.add(expense)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing = self.expenses.find_by_client_operation(data.client_operation_id, user.id)
            if existing is None:
                raise
            self._ensure_equivalent(existing, data, category.id)
            return existing, False
        return expense, True

    def update(self, public_id: uuid.UUID, values: dict, user: User) -> Expense:
        expense = self.get(public_id, user)
        category_public_id = values.pop("category_public_id", None)
        if category_public_id is not None:
            category = self.categories.find_visible(category_public_id, user.id)
            if category is None:
                raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
            expense.category_id = category.id
            expense.category = category
        for field, value in values.items():
            setattr(expense, field, value)
        db.session.commit()
        return expense

    def delete(self, public_id: uuid.UUID, user: User) -> None:
        expense = self.get(public_id, user)
        expense.deleted_at = datetime.now(UTC)
        db.session.commit()

    @staticmethod
    def _ensure_equivalent(expense: Expense, data: ExpenseData, category_id: int) -> None:
        values_match = (
            expense.category_id == category_id
            and expense.amount == data.amount
            and expense.currency == data.currency
            and expense.expense_date == data.expense_date
            and expense.merchant == data.merchant
            and expense.description == data.description
            and expense.comment == data.comment
            and expense.source == data.source
        )
        if not values_match:
            raise ApiError(
                "CLIENT_OPERATION_CONFLICT",
                "client_operation_id уже использован с другими данными",
                409,
            )

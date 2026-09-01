import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.extensions import db
from app.models import Budget, User
from app.repositories.budgets import BudgetRepository
from app.repositories.categories import CategoryRepository

CENT = Decimal("0.01")


class BudgetService:
    def __init__(self) -> None:
        self.budgets = BudgetRepository()
        self.categories = CategoryRepository()

    def list(self, user: User) -> list[dict]:
        return [self._result(budget) for budget in self.budgets.list(user.id)]

    def get(self, public_id: uuid.UUID, user: User) -> Budget:
        budget = self.budgets.find(public_id, user.id)
        if budget is None:
            raise ApiError("BUDGET_NOT_FOUND", "Бюджет не найден", 404)
        return budget

    def get_result(self, public_id: uuid.UUID, user: User) -> dict:
        return self._result(self.get(public_id, user))

    def create(self, values: dict, user: User) -> dict:
        category = self._category(values.pop("category_public_id"), user)
        self._validate_dates(values["start_date"], values["end_date"])
        budget = Budget(
            user_id=user.id,
            category_id=category.id,
            category=category,
            currency=values.pop("currency", "RUB"),
            **values,
        )
        self._ensure_unique(budget)
        db.session.add(budget)
        self._commit_unique()
        return self._result(budget)

    def update(self, public_id: uuid.UUID, values: dict, user: User) -> dict:
        budget = self.get(public_id, user)
        category_id = values.pop("category_public_id", None)
        if category_id is not None:
            category = self._category(category_id, user)
            budget.category_id, budget.category = category.id, category
        for field, value in values.items():
            setattr(budget, field, value)
        self._validate_dates(budget.start_date, budget.end_date)
        self._ensure_unique(budget)
        self._commit_unique()
        return self._result(budget)

    def delete(self, public_id: uuid.UUID, user: User) -> None:
        db.session.delete(self.get(public_id, user))
        db.session.commit()

    def _result(self, budget: Budget) -> dict:
        spent = self.budgets.spent(budget)
        remaining = budget.amount - spent
        usage = (spent / budget.amount * 100).quantize(CENT, rounding=ROUND_HALF_UP)
        reached = {event.threshold for event in budget.threshold_events}
        for threshold in (80, 100):
            if usage >= threshold and threshold not in reached:
                self.budgets.add_event(budget, threshold)
                reached.add(threshold)
        if db.session.new:
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                budget = self.budgets.find(budget.public_id, budget.user_id) or budget
                reached = {event.threshold for event in budget.threshold_events}
        return {
            "id": str(budget.public_id),
            "category_id": str(budget.category.public_id),
            "category_name": budget.category.name,
            "amount": self._money(budget.amount),
            "currency": budget.currency,
            "period": budget.period,
            "start_date": budget.start_date.isoformat(),
            "end_date": budget.end_date.isoformat(),
            "spent": self._money(spent),
            "remaining": self._money(remaining),
            "usage_percent": format(usage, ".2f"),
            "thresholds_reached": sorted(reached),
            "created_at": budget.created_at.isoformat(),
            "updated_at": budget.updated_at.isoformat(),
        }

    def _category(self, public_id: uuid.UUID, user: User):  # type: ignore[no-untyped-def]
        category = self.categories.find_visible(public_id, user.id)
        if category is None:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
        return category

    def _ensure_unique(self, budget: Budget) -> None:
        duplicate = self.budgets.duplicate(
            budget.user_id, budget.category_id, budget.start_date, budget.end_date, budget.id
        )
        if duplicate is not None:
            raise ApiError(
                "BUDGET_ALREADY_EXISTS", "Бюджет для категории и периода уже существует", 409
            )

    @staticmethod
    def _validate_dates(start, end) -> None:  # type: ignore[no-untyped-def]
        if start > end:
            raise ApiError(
                "VALIDATION_ERROR",
                "Начало периода позже окончания",
                400,
                {"end_date": ["Некорректный период"]},
            )

    @staticmethod
    def _money(value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")

    @staticmethod
    def _commit_unique() -> None:
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ApiError(
                "BUDGET_ALREADY_EXISTS", "Бюджет для категории и периода уже существует", 409
            ) from error

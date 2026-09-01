import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Budget, BudgetThresholdEvent, Expense


class BudgetRepository:
    def list(self, user_id: int) -> list[Budget]:
        return list(
            db.session.scalars(
                select(Budget)
                .options(joinedload(Budget.category), joinedload(Budget.threshold_events))
                .where(Budget.user_id == user_id)
                .order_by(Budget.start_date.desc())
            ).unique()
        )

    def find(self, public_id: uuid.UUID, user_id: int) -> Budget | None:
        return db.session.scalar(
            select(Budget)
            .options(joinedload(Budget.category), joinedload(Budget.threshold_events))
            .where(Budget.public_id == public_id, Budget.user_id == user_id)
        )

    def spent(self, budget: Budget) -> Decimal:
        value = db.session.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == budget.user_id,
                Expense.category_id == budget.category_id,
                Expense.currency == budget.currency,
                Expense.deleted_at.is_(None),
                Expense.expense_date.between(budget.start_date, budget.end_date),
            )
        )
        return Decimal(value or 0)

    def add_event(self, budget: Budget, threshold: int) -> None:
        db.session.add(BudgetThresholdEvent(budget=budget, threshold=threshold))

    def duplicate(
        self, user_id: int, category_id: int, start: date, end: date, exclude_id: int | None = None
    ) -> Budget | None:
        query = select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.start_date == start,
            Budget.end_date == end,
        )
        if exclude_id is not None:
            query = query.where(Budget.id != exclude_id)
        return db.session.scalar(query)

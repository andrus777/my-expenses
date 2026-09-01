from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select

from app.extensions import db
from app.models import Category, Expense, Subscription


class StatisticsRepository:
    def expense_totals(
        self, user_id: int, date_from: date, date_to: date, currency: str
    ) -> tuple[Decimal, int]:
        total, count = db.session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(
                Expense.user_id == user_id,
                Expense.deleted_at.is_(None),
                Expense.expense_date.between(date_from, date_to),
                Expense.currency == currency,
            )
        ).one()
        return Decimal(total), int(count)

    def categories(
        self, user_id: int, date_from: date, date_to: date, currency: str
    ) -> list[tuple]:
        return list(
            db.session.execute(
                select(
                    Category.public_id,
                    Category.name,
                    func.sum(Expense.amount).label("total"),
                    func.count(Expense.id).label("operations_count"),
                )
                .join(Expense, Expense.category_id == Category.id)
                .where(
                    Expense.user_id == user_id,
                    Expense.deleted_at.is_(None),
                    Expense.expense_date.between(date_from, date_to),
                    Expense.currency == currency,
                )
                .group_by(Category.id, Category.public_id, Category.name)
                .order_by(func.sum(Expense.amount).desc(), Category.name)
            )
        )

    def daily_totals(
        self, user_id: int, date_from: date, date_to: date, currency: str
    ) -> list[tuple[date, Decimal, int]]:
        rows = db.session.execute(
            select(
                Expense.expense_date,
                func.sum(Expense.amount),
                func.count(Expense.id),
            )
            .where(
                Expense.user_id == user_id,
                Expense.deleted_at.is_(None),
                Expense.expense_date.between(date_from, date_to),
                Expense.currency == currency,
            )
            .group_by(Expense.expense_date)
            .order_by(Expense.expense_date)
        )
        return [(row[0], Decimal(row[1]), int(row[2])) for row in rows]

    def subscription_totals(self, user_id: int, currency: str) -> tuple[Decimal, Decimal, int]:
        monthly_factor = case(
            (Subscription.frequency == "WEEKLY", Decimal("52") / Decimal("12")),
            (Subscription.frequency == "MONTHLY", Decimal("1")),
            (Subscription.frequency == "QUARTERLY", Decimal("1") / Decimal("3")),
            (Subscription.frequency == "HALF_YEAR", Decimal("1") / Decimal("6")),
            (Subscription.frequency == "YEARLY", Decimal("1") / Decimal("12")),
            (
                Subscription.frequency == "CUSTOM",
                Decimal("30.4375") / func.nullif(Subscription.custom_interval_days, 0),
            ),
            else_=Decimal("0"),
        )
        monthly, yearly, count = db.session.execute(
            select(
                func.coalesce(func.sum(Subscription.amount * monthly_factor), 0),
                func.coalesce(func.sum(Subscription.amount * monthly_factor * 12), 0),
                func.count(Subscription.id),
            ).where(
                Subscription.user_id == user_id,
                Subscription.deleted_at.is_(None),
                Subscription.is_active.is_(True),
                Subscription.currency == currency,
            )
        ).one()
        return Decimal(monthly), Decimal(yearly), int(count)

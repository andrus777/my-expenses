from collections import defaultdict
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.models import User
from app.repositories.statistics import StatisticsRepository
from app.schemas.statistics import StatisticsPeriod

CENT = Decimal("0.01")


def money(value: Decimal) -> str:
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


class StatisticsService:
    def __init__(self) -> None:
        self.repository = StatisticsRepository()

    def summary(self, user: User, period: StatisticsPeriod, currency: str) -> dict:
        total, count = self.repository.expense_totals(
            user.id, period.date_from, period.date_to, currency
        )
        previous_total, _ = self.repository.expense_totals(
            user.id, period.previous.date_from, period.previous.date_to, currency
        )
        change = None
        if previous_total != 0:
            change = ((total - previous_total) / previous_total * 100).quantize(CENT)
        return {
            "date_from": period.date_from.isoformat(),
            "date_to": period.date_to.isoformat(),
            "currency": currency,
            "total": money(total),
            "operations_count": count,
            "average_daily": money(total / period.days),
            "previous_period_total": money(previous_total),
            "change_percent": format(change, ".2f") if change is not None else None,
        }

    def categories(self, user: User, period: StatisticsPeriod, currency: str) -> dict:
        rows = self.repository.categories(user.id, period.date_from, period.date_to, currency)
        grand_total = sum((Decimal(row.total) for row in rows), Decimal("0"))
        return {
            "date_from": period.date_from.isoformat(),
            "date_to": period.date_to.isoformat(),
            "currency": currency,
            "items": [
                {
                    "category_id": str(row.public_id),
                    "category_name": row.name,
                    "total": money(Decimal(row.total)),
                    "operations_count": int(row.operations_count),
                    "percent": format(
                        (Decimal(row.total) / grand_total * 100).quantize(CENT), ".2f"
                    )
                    if grand_total
                    else "0.00",
                }
                for row in rows
            ],
        }

    def timeline(self, user: User, period: StatisticsPeriod, interval: str, currency: str) -> dict:
        buckets: dict[date, list] = defaultdict(lambda: [Decimal("0"), 0])
        for expense_date, total, count in self.repository.daily_totals(
            user.id, period.date_from, period.date_to, currency
        ):
            bucket = self._bucket(expense_date, interval)
            buckets[bucket][0] += total
            buckets[bucket][1] += count
        cursor = self._bucket(period.date_from, interval)
        end = self._bucket(period.date_to, interval)
        items = []
        while cursor <= end:
            total, count = buckets[cursor]
            items.append(
                {"period": cursor.isoformat(), "total": money(total), "operations_count": count}
            )
            cursor = self._next_bucket(cursor, interval)
        return {"interval": interval, "currency": currency, "items": items}

    def subscriptions(self, user: User, currency: str) -> dict:
        monthly, yearly, count = self.repository.subscription_totals(user.id, currency)
        return {
            "currency": currency,
            "monthly_total": money(monthly),
            "yearly_total": money(yearly),
            "active_count": count,
        }

    @staticmethod
    def _bucket(value: date, interval: str) -> date:
        if interval == "week":
            return value - timedelta(days=value.weekday())
        if interval == "month":
            return value.replace(day=1)
        return value

    @staticmethod
    def _next_bucket(value: date, interval: str) -> date:
        if interval == "week":
            return value + timedelta(days=7)
        if interval == "month":
            return date(value.year + (value.month == 12), value.month % 12 + 1, 1)
        return value + timedelta(days=1)

from datetime import date

from app.analytics.service import StatisticsService
from app.schemas.statistics import StatisticsPeriod


def test_previous_period_preserves_length_across_year_boundary():
    period = StatisticsPeriod(date(2026, 1, 1), date(2026, 1, 7))
    assert period.days == 7
    assert period.previous == StatisticsPeriod(date(2025, 12, 25), date(2025, 12, 31))


def test_week_and_month_buckets_have_calendar_boundaries():
    assert StatisticsService._bucket(date(2026, 1, 1), "week") == date(2025, 12, 29)
    assert StatisticsService._next_bucket(date(2024, 2, 1), "month") == date(2024, 3, 1)
    assert StatisticsService._next_bucket(date(2026, 12, 1), "month") == date(2027, 1, 1)

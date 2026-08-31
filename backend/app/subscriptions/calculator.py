import calendar
from datetime import date, timedelta

FREQUENCY_MONTHS = {"MONTHLY": 1, "QUARTERLY": 3, "HALF_YEAR": 6, "YEARLY": 12}
FREQUENCIES = {"WEEKLY", *FREQUENCY_MONTHS, "CUSTOM"}


def calculate_next_payment_date(
    current: date,
    frequency: str,
    billing_day: int,
    custom_interval_days: int | None = None,
) -> date:
    if frequency == "WEEKLY":
        return current + timedelta(days=7)
    if frequency == "CUSTOM":
        if custom_interval_days is None or custom_interval_days < 1:
            raise ValueError("custom_interval_days must be positive")
        return current + timedelta(days=custom_interval_days)
    months = FREQUENCY_MONTHS.get(frequency)
    if months is None:
        raise ValueError("unknown frequency")
    month_index = current.year * 12 + current.month - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(billing_day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

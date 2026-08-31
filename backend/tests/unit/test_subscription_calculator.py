from datetime import date

import pytest

from app.subscriptions.calculator import calculate_next_payment_date


@pytest.mark.parametrize(
    ("current", "frequency", "billing_day", "expected"),
    [
        (date(2026, 1, 31), "MONTHLY", 31, date(2026, 2, 28)),
        (date(2026, 2, 28), "MONTHLY", 31, date(2026, 3, 31)),
        (date(2024, 2, 29), "YEARLY", 29, date(2025, 2, 28)),
        (date(2027, 2, 28), "YEARLY", 29, date(2028, 2, 29)),
        (date(2026, 11, 30), "QUARTERLY", 30, date(2027, 2, 28)),
        (date(2026, 8, 31), "HALF_YEAR", 31, date(2027, 2, 28)),
        (date(2026, 8, 31), "WEEKLY", 31, date(2026, 9, 7)),
    ],
)
def test_next_payment_edge_cases(current, frequency, billing_day, expected):
    assert calculate_next_payment_date(current, frequency, billing_day) == expected


def test_custom_frequency():
    assert calculate_next_payment_date(date(2026, 1, 1), "CUSTOM", 1, 45) == date(2026, 2, 15)


def test_custom_frequency_requires_positive_interval():
    with pytest.raises(ValueError):
        calculate_next_payment_date(date(2026, 1, 1), "CUSTOM", 1, 0)

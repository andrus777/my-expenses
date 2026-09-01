from dataclasses import dataclass
from datetime import date, timedelta

from flask import request

from app.api.errors import ApiError


@dataclass(frozen=True)
class StatisticsPeriod:
    date_from: date
    date_to: date

    @property
    def days(self) -> int:
        return (self.date_to - self.date_from).days + 1

    @property
    def previous(self) -> "StatisticsPeriod":
        previous_to = self.date_from - timedelta(days=1)
        return StatisticsPeriod(previous_to - timedelta(days=self.days - 1), previous_to)


def parse_period() -> StatisticsPeriod:
    today = date.today()
    date_to = _date_argument("date_to") or today
    date_from = _date_argument("date_from") or date_to - timedelta(days=29)
    if date_from > date_to:
        raise ApiError(
            "VALIDATION_ERROR",
            "date_from не может быть позже date_to",
            400,
            {"date_from": ["Некорректный диапазон"]},
        )
    if (date_to - date_from).days > 3660:
        raise ApiError("VALIDATION_ERROR", "Период не может превышать 10 лет", 400)
    return StatisticsPeriod(date_from, date_to)


def parse_interval(period: StatisticsPeriod) -> str:
    interval = request.args.get("interval")
    if interval is None:
        return "day" if period.days <= 31 else "week" if period.days <= 180 else "month"
    if interval not in {"day", "week", "month"}:
        raise ApiError(
            "VALIDATION_ERROR",
            "interval должен быть day, week или month",
            400,
            {"interval": ["Недопустимое значение"]},
        )
    return interval


def parse_currency() -> str:
    currency = request.args.get("currency", "RUB").strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ApiError(
            "VALIDATION_ERROR", "Некорректный код валюты", 400, {"currency": ["Ожидается ISO 4217"]}
        )
    return currency


def _date_argument(name: str) -> date | None:
    value = request.args.get(name)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Некорректная дата", 400, {name: ["Ожидается YYYY-MM-DD"]}
        ) from error

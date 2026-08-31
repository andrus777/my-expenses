import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.api.errors import ApiError
from app.schemas.common import parse_amount, parse_date, parse_optional_text, parse_uuid
from app.subscriptions.calculator import FREQUENCIES


@dataclass(frozen=True)
class SubscriptionData:
    name: str
    category_public_id: uuid.UUID
    amount: Decimal
    currency: str
    frequency: str
    custom_interval_days: int | None
    next_payment_date: date
    comment: str | None
    is_active: bool


def parse_subscription(payload: object, partial: bool = False) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    allowed = {
        "name",
        "category_id",
        "amount",
        "currency",
        "frequency",
        "custom_interval_days",
        "next_payment_date",
        "comment",
        "is_active",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {key: ["Неизвестное поле"] for key in sorted(unknown)},
        )
    required = {"name", "category_id", "amount", "frequency", "next_payment_date"}
    missing = required - set(payload) if not partial else set()
    if missing:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {key: ["Обязательное поле"] for key in sorted(missing)},
        )
    values: dict = {}
    if "name" in payload:
        name = payload["name"]
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 150:
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"name": ["Некорректное название"]}
            )
        values["name"] = name.strip()
    if "category_id" in payload:
        values["category_public_id"] = parse_uuid(payload["category_id"], "category_id")
    if "amount" in payload:
        values["amount"] = parse_amount(payload["amount"])
    if "currency" in payload:
        currency = payload["currency"]
        if not isinstance(currency, str) or len(currency.strip()) != 3 or not currency.isalpha():
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"currency": ["Некорректная валюта"]}
            )
        values["currency"] = currency.upper()
    if "frequency" in payload:
        frequency = payload["frequency"]
        if frequency not in FREQUENCIES:
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"frequency": ["Неизвестная частота"]}
            )
        values["frequency"] = frequency
    if "custom_interval_days" in payload:
        interval = payload["custom_interval_days"]
        if interval is not None and (
            not isinstance(interval, int) or isinstance(interval, bool) or interval < 1
        ):
            raise ApiError(
                "VALIDATION_ERROR",
                "Ошибка валидации",
                400,
                {"custom_interval_days": ["Укажите положительное число дней"]},
            )
        values["custom_interval_days"] = interval
    if "next_payment_date" in payload:
        values["next_payment_date"] = parse_date(payload["next_payment_date"], "next_payment_date")
    if "comment" in payload:
        values["comment"] = parse_optional_text(payload["comment"], "comment", None)
    if "is_active" in payload:
        if not isinstance(payload["is_active"], bool):
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"is_active": ["Ожидается boolean"]}
            )
        values["is_active"] = payload["is_active"]
    return values


def parse_payment(payload: object) -> tuple[uuid.UUID, date | None]:
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    if "client_operation_id" not in payload:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {"client_operation_id": ["Обязательное поле"]},
        )
    operation_id = parse_uuid(payload["client_operation_id"], "client_operation_id")
    payment_date = (
        parse_date(payload["payment_date"], "payment_date") if "payment_date" in payload else None
    )
    return operation_id, payment_date

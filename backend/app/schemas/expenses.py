import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.api.errors import ApiError
from app.schemas.common import parse_amount, parse_date, parse_optional_text, parse_uuid

ALLOWED_SOURCES = {"MANUAL", "RECEIPT", "SUBSCRIPTION", "SYNC"}
EDITABLE_FIELDS = {
    "category_id",
    "amount",
    "currency",
    "expense_date",
    "merchant",
    "description",
    "comment",
}


@dataclass(frozen=True)
class ExpenseData:
    category_public_id: uuid.UUID
    amount: Decimal
    currency: str
    expense_date: date
    merchant: str | None
    description: str | None
    comment: str | None
    source: str
    client_operation_id: uuid.UUID


def _parse_currency(value: object) -> str:
    if not isinstance(value, str) or len(value.strip()) != 3 or not value.strip().isalpha():
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {"currency": ["Используйте трёхбуквенный код валюты"]},
        )
    return value.strip().upper()


def parse_expense_create(payload: object) -> ExpenseData:
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    required = {"category_id", "amount", "expense_date", "client_operation_id"}
    missing = sorted(field for field in required if field not in payload)
    if missing:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: ["Обязательное поле"] for field in missing},
        )
    source = payload.get("source", "MANUAL")
    if not isinstance(source, str) or source.upper() not in ALLOWED_SOURCES:
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {"source": ["Неизвестный источник"]}
        )
    return ExpenseData(
        category_public_id=parse_uuid(payload["category_id"], "category_id"),
        amount=parse_amount(payload["amount"]),
        currency=_parse_currency(payload.get("currency", "RUB")),
        expense_date=parse_date(payload["expense_date"], "expense_date"),
        merchant=parse_optional_text(payload.get("merchant"), "merchant", 255),
        description=parse_optional_text(payload.get("description"), "description", 500),
        comment=parse_optional_text(payload.get("comment"), "comment", None),
        source=source.upper(),
        client_operation_id=parse_uuid(payload["client_operation_id"], "client_operation_id"),
    )


def parse_expense_patch(payload: object) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    unknown = sorted(set(payload) - EDITABLE_FIELDS)
    if unknown:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: ["Поле нельзя изменить"] for field in unknown},
        )
    values: dict = {}
    if "category_id" in payload:
        values["category_public_id"] = parse_uuid(payload["category_id"], "category_id")
    if "amount" in payload:
        values["amount"] = parse_amount(payload["amount"])
    if "currency" in payload:
        values["currency"] = _parse_currency(payload["currency"])
    if "expense_date" in payload:
        values["expense_date"] = parse_date(payload["expense_date"], "expense_date")
    for field, max_length in (("merchant", 255), ("description", 500), ("comment", None)):
        if field in payload:
            values[field] = parse_optional_text(payload[field], field, max_length)
    return values

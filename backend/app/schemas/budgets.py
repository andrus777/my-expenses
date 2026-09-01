from app.api.errors import ApiError
from app.schemas.common import parse_amount, parse_date, parse_uuid

PERIODS = {"WEEK", "MONTH", "YEAR", "CUSTOM"}


def parse_budget(payload: object, partial: bool = False) -> dict:
    if not isinstance(payload, dict) or not payload:
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    allowed = {"category_id", "amount", "currency", "period", "start_date", "end_date"}
    unknown = set(payload) - allowed
    if unknown:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {key: ["Неизвестное поле"] for key in sorted(unknown)},
        )
    required = {"category_id", "amount", "period", "start_date", "end_date"}
    missing = required - set(payload) if not partial else set()
    if missing:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {key: ["Обязательное поле"] for key in sorted(missing)},
        )
    values = {}
    if "category_id" in payload:
        values["category_public_id"] = parse_uuid(payload["category_id"], "category_id")
    if "amount" in payload:
        values["amount"] = parse_amount(payload["amount"])
    if "currency" in payload:
        currency = payload["currency"]
        if (
            not isinstance(currency, str)
            or len(currency.strip()) != 3
            or not currency.strip().isalpha()
        ):
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"currency": ["Некорректная валюта"]}
            )
        values["currency"] = currency.strip().upper()
    if "period" in payload:
        period = payload["period"]
        if period not in PERIODS:
            raise ApiError(
                "VALIDATION_ERROR", "Ошибка валидации", 400, {"period": ["Неизвестный период"]}
            )
        values["period"] = period
    for field in ("start_date", "end_date"):
        if field in payload:
            values[field] = parse_date(payload[field], field)
    return values

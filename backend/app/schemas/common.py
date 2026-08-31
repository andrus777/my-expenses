import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from app.api.errors import ApiError


def parse_uuid(value: object, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Некорректный UUID"]}
        ) from error


def parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Укажите дату ISO 8601"]}
        )
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Некорректная дата"]}
        ) from error


def parse_amount(value: object, field: str = "amount") -> Decimal:
    if not isinstance(value, str):
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: ["Денежное значение должно быть строкой"]},
        )
    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Некорректная сумма"]}
        ) from error
    if not amount.is_finite() or amount <= 0:
        raise ApiError(
            "VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Сумма должна быть больше 0"]}
        )
    if amount.as_tuple().exponent < -2 or amount.adjusted() > 15:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: ["Сумма должна иметь не более 2 десятичных знаков и 16 целых цифр"]},
        )
    return amount.quantize(Decimal("0.01"))


def parse_optional_text(value: object, field: str, max_length: int | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError("VALIDATION_ERROR", "Ошибка валидации", 400, {field: ["Ожидается строка"]})
    normalized = value.strip()
    if not normalized:
        return None
    if max_length is not None and len(normalized) > max_length:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: [f"Максимальная длина: {max_length}"]},
        )
    return normalized

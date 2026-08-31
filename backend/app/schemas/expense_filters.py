from flask import Request

from app.api.errors import ApiError
from app.repositories.expenses import ExpenseFilters
from app.schemas.common import parse_amount, parse_date, parse_uuid
from app.schemas.expenses import ALLOWED_SOURCES


def _positive_int(value: str | None, default: int, maximum: int | None = None) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise ApiError("VALIDATION_ERROR", "Некорректные параметры запроса", 400) from error
    if parsed < 1 or (maximum is not None and parsed > maximum):
        raise ApiError("VALIDATION_ERROR", "Некорректные параметры запроса", 400)
    return parsed


def parse_expense_filters(request: Request) -> ExpenseFilters:
    args = request.args
    sort = args.get("sort", "expense_date")
    order = args.get("order", "desc")
    if sort not in {"expense_date", "amount", "created_at"} or order not in {"asc", "desc"}:
        raise ApiError("VALIDATION_ERROR", "Некорректная сортировка", 400)
    source = args.get("source")
    if source is not None:
        source = source.upper()
        if source not in ALLOWED_SOURCES:
            raise ApiError("VALIDATION_ERROR", "Неизвестный источник", 400)
    currency = args.get("currency")
    if currency is not None:
        currency = currency.upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ApiError("VALIDATION_ERROR", "Некорректная валюта", 400)
    search = args.get("search")
    if search is not None:
        search = search.strip()
        if len(search) > 100:
            raise ApiError("VALIDATION_ERROR", "Слишком длинный поисковый запрос", 400)
    return ExpenseFilters(
        page=_positive_int(args.get("page"), 1),
        per_page=_positive_int(args.get("per_page"), 20, 100),
        date_from=parse_date(args["date_from"], "date_from") if "date_from" in args else None,
        date_to=parse_date(args["date_to"], "date_to") if "date_to" in args else None,
        category_public_id=(
            parse_uuid(args["category_id"], "category_id") if "category_id" in args else None
        ),
        min_amount=parse_amount(args["min_amount"], "min_amount") if "min_amount" in args else None,
        max_amount=parse_amount(args["max_amount"], "max_amount") if "max_amount" in args else None,
        currency=currency,
        source=source,
        search=search or None,
        sort=sort,
        order=order,
    )

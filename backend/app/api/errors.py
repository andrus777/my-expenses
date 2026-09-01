from typing import Any

from flask import Flask, g, jsonify
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_response(
    code: str, message: str, status_code: int, details: dict[str, Any] | None = None
):
    if not getattr(g, "request_id", None):
        from uuid import uuid4

        g.request_id = str(uuid4())
    return (
        jsonify(
            {
                "error": {"code": code, "message": message, "details": details or {}},
                "request_id": getattr(g, "request_id", None),
            }
        ),
        status_code,
    )


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):  # type: ignore[no-untyped-def]
        return error_response(error.code, error.message, error.status_code, error.details)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(_error: RateLimitExceeded):  # type: ignore[no-untyped-def]
        return error_response("RATE_LIMIT_EXCEEDED", "Слишком много запросов", 429)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):  # type: ignore[no-untyped-def]
        status = error.code or 500
        code, message = {
            400: ("VALIDATION_ERROR", "Некорректный запрос"),
            401: ("AUTHENTICATION_REQUIRED", "Требуется авторизация"),
            403: ("FORBIDDEN", "Доступ запрещён"),
            404: ("NOT_FOUND", "Ресурс не найден"),
            409: ("CONFLICT", "Конфликт состояния ресурса"),
        }.get(status, ("HTTP_ERROR", error.description))
        return error_response(code, message, status)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # type: ignore[no-untyped-def]
        app.logger.error(
            "unhandled application error",
            extra={
                "event": "unhandled_error",
                "request_id": getattr(g, "request_id", None),
            },
        )
        return error_response("INTERNAL_ERROR", "Внутренняя ошибка сервера", 500)

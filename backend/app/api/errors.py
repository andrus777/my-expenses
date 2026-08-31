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
        return error_response("HTTP_ERROR", error.description, error.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):  # type: ignore[no-untyped-def]
        app.logger.exception("Unhandled application error", exc_info=error)
        return error_response("INTERNAL_ERROR", "Внутренняя ошибка сервера", 500)

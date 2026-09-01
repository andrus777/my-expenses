import json
import logging
import re
import time
from datetime import UTC, datetime
from uuid import uuid4

from flask import Flask, g, request
from flask_jwt_extended import get_jwt_identity

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
LOG_FIELDS = (
    "event",
    "request_id",
    "user_id",
    "method",
    "path",
    "status",
    "duration_ms",
    "dependency",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(app: Flask) -> None:
    configured = str(app.config["LOG_LEVEL"]).upper()
    level = getattr(logging, configured, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    app.logger.propagate = False


def register_request_observability(app: Flask) -> None:
    @app.before_request
    def start_request() -> None:
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid4())
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):  # type: ignore[no-untyped-def]
        started = getattr(g, "request_started_at", time.perf_counter())
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        user_id = getattr(g, "user_id", None)
        if user_id is None:
            try:
                user_id = get_jwt_identity()
            except RuntimeError:
                user_id = None
        app.logger.info(
            "request completed",
            extra={
                "event": "http_request",
                "request_id": g.request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

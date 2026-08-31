import logging
import time
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from flask import Flask, g, request

from app.api import health_blueprint
from app.api.errors import register_error_handlers
from app.api.v1 import api_v1_blueprint
from app.auth.jwt_callbacks import register_jwt_callbacks
from app.celery_app import init_celery
from app.config import get_config
from app.extensions import db, jwt, limiter, migrate, redis_client


def create_app(config: str | Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config if isinstance(config, str) else None))
    if isinstance(config, Mapping):
        app.config.from_mapping(config)

    _configure_logging(app)
    db.init_app(app)
    migrate.init_app(app, db)
    redis_client.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    init_celery(app)
    app.register_blueprint(health_blueprint)
    app.register_blueprint(api_v1_blueprint)
    register_jwt_callbacks(jwt)
    register_error_handlers(app)
    _register_request_observability(app)
    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(level=level)


def _register_request_observability(app: Flask) -> None:
    @app.before_request
    def start_request() -> None:
        g.request_id = request.headers.get("X-Request-ID") or str(uuid4())
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):  # type: ignore[no-untyped-def]
        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        app.logger.info(
            "request completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
            g.request_id,
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response


__all__ = ["create_app"]

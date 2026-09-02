from collections.abc import Mapping
from typing import Any

from flask import Flask

from app.api import health_blueprint
from app.api.errors import register_error_handlers
from app.api.v1 import api_v1_blueprint
from app.auth.jwt_callbacks import register_jwt_callbacks
from app.celery_app import init_celery
from app.config import get_config
from app.dev_seed import register_seed_command
from app.extensions import db, jwt, limiter, migrate, redis_client
from app.observability import configure_logging, register_request_observability


def create_app(config: str | Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config if isinstance(config, str) else None))
    if isinstance(config, Mapping):
        app.config.from_mapping(config)

    configure_logging(app)
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
    register_request_observability(app)
    register_seed_command(app)
    return app


__all__ = ["create_app"]

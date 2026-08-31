from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db, redis_client

blueprint = Blueprint("health", __name__)


@blueprint.get("/health")
def health():  # type: ignore[no-untyped-def]
    return jsonify({"status": "ok"})


@blueprint.get("/ready")
def ready():  # type: ignore[no-untyped-def]
    checks: dict[str, str] = {}

    try:
        db.session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        current_app.logger.exception("PostgreSQL readiness check failed")
        checks["postgres"] = "unavailable"

    try:
        redis_client.get(current_app).ping()
        checks["redis"] = "ok"
    except Exception:
        current_app.logger.exception("Redis readiness check failed")
        checks["redis"] = "unavailable"

    is_ready = all(result == "ok" for result in checks.values())
    return jsonify({"status": "ready" if is_ready else "not_ready", "checks": checks}), (
        200 if is_ready else 503
    )

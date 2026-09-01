from flask import Blueprint, current_app, g, jsonify
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
        if db.session.get_bind().dialect.name == "postgresql":
            db.session.execute(
                text("SET LOCAL statement_timeout = :timeout_ms"),
                {"timeout_ms": current_app.config["READINESS_DB_TIMEOUT_MS"]},
            )
        db.session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        db.session.rollback()
        current_app.logger.warning(
            "readiness dependency unavailable",
            extra={
                "event": "readiness_check",
                "dependency": "postgres",
                "request_id": g.request_id,
            },
        )
        checks["postgres"] = "unavailable"

    try:
        redis_client.get(current_app).ping()
        checks["redis"] = "ok"
    except Exception:
        current_app.logger.warning(
            "readiness dependency unavailable",
            extra={
                "event": "readiness_check",
                "dependency": "redis",
                "request_id": g.request_id,
            },
        )
        checks["redis"] = "unavailable"

    is_ready = all(result == "ok" for result in checks.values())
    payload = {"status": "ready" if is_ready else "not_ready", "checks": checks}
    if not is_ready:
        payload["request_id"] = g.request_id
    return jsonify(payload), 200 if is_ready else 503

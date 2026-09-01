import io
import json
import logging
from unittest.mock import Mock, patch

from app.observability import JsonFormatter


def _assert_error_contract(response, code, request_id=None):
    assert set(response.json) == {"error", "request_id"}
    assert response.json["error"]["code"] == code
    assert set(response.json["error"]) == {"code", "message", "details"}
    assert response.json["request_id"]
    assert response.headers["X-Request-ID"] == response.json["request_id"]
    if request_id:
        assert response.json["request_id"] == request_id


def test_validation_auth_not_found_and_conflict_share_error_contract(client, auth_client):
    request_id = "mobile-01HZZ.test"
    validation = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid", "password": "short"},
        headers={"X-Request-ID": request_id},
    )
    authentication = client.get("/api/v1/users/me")
    not_found = client.get("/api/v1/does-not-exist")
    auth_client("duplicate-observability@example.com")
    conflict = client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate-observability@example.com", "password": "secure-password"},
    )

    _assert_error_contract(validation, "VALIDATION_ERROR", request_id)
    _assert_error_contract(authentication, "AUTHENTICATION_REQUIRED")
    _assert_error_contract(not_found, "NOT_FOUND")
    _assert_error_contract(conflict, "EMAIL_ALREADY_EXISTS")


def test_unsafe_request_id_is_replaced(client):
    unsafe = "request id with spaces/unsafe"
    response = client.get("/missing", headers={"X-Request-ID": unsafe})

    _assert_error_contract(response, "NOT_FOUND")
    assert response.json["request_id"] != unsafe


def test_internal_error_uses_contract_without_exposing_exception(app, client):
    @app.get("/test-internal-error")
    def fail():
        raise RuntimeError("private-provider-key")

    response = client.get("/test-internal-error", headers={"X-Request-ID": "internal-test"})

    assert response.status_code == 500
    _assert_error_contract(response, "INTERNAL_ERROR", "internal-test")
    assert "private-provider-key" not in response.get_data(as_text=True)


def test_structured_request_log_contains_safe_fields_not_credentials(app, client):
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonFormatter())
    app.logger.handlers[:] = [handler]

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "logs@example.com", "password": "never-log-this-password"},
        headers={"X-Request-ID": "structured-log", "Authorization": "Bearer secret-token"},
    )

    assert response.status_code == 201
    log = json.loads(output.getvalue().splitlines()[-1])
    assert log["event"] == "http_request"
    assert log["request_id"] == "structured-log"
    assert log["method"] == "POST"
    assert log["path"] == "/api/v1/auth/register"
    assert log["status"] == 201
    assert isinstance(log["duration_ms"], float)
    serialized = output.getvalue()
    assert "never-log-this-password" not in serialized
    assert "secret-token" not in serialized
    assert "Authorization" not in serialized


def test_readiness_reports_each_dependency_without_error_details(client):
    redis = Mock()
    redis.ping.side_effect = TimeoutError("redis://user:password@private-host")
    with (
        patch("app.api.health.db.session.execute", side_effect=TimeoutError("db password")),
        patch("app.api.health.redis_client.get", return_value=redis),
    ):
        response = client.get("/ready", headers={"X-Request-ID": "ready-failed"})

    assert response.status_code == 503
    assert response.json == {
        "status": "not_ready",
        "checks": {"postgres": "unavailable", "redis": "unavailable"},
        "request_id": "ready-failed",
    }
    assert response.headers["X-Request-ID"] == "ready-failed"
    assert "password" not in response.get_data(as_text=True)


def test_liveness_does_not_check_dependencies(client):
    with (
        patch("app.api.health.db.session.execute") as database,
        patch("app.api.health.redis_client.get") as redis,
    ):
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    database.assert_not_called()
    redis.assert_not_called()

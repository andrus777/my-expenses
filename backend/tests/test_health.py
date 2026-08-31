from unittest.mock import Mock, patch


def test_health_returns_ok_and_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "test-request-id"


def test_health_generates_request_id(client):
    response = client.get("/health")

    assert response.headers["X-Request-ID"]


def test_ready_returns_success_when_dependencies_are_available(app, client):
    redis = Mock()
    redis.ping.return_value = True

    with (
        patch("app.api.health.db.session.execute") as execute,
        patch("app.api.health.redis_client.get", return_value=redis),
    ):
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json == {
        "status": "ready",
        "checks": {"postgres": "ok", "redis": "ok"},
    }
    execute.assert_called_once()
    redis.ping.assert_called_once_with()


def test_ready_returns_503_when_a_dependency_is_unavailable(app, client):
    redis = Mock()
    redis.ping.side_effect = ConnectionError("Redis unavailable")

    with (
        patch("app.api.health.db.session.execute"),
        patch("app.api.health.redis_client.get", return_value=redis),
    ):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json == {
        "status": "not_ready",
        "checks": {"postgres": "ok", "redis": "unavailable"},
    }

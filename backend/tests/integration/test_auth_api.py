from app import create_app
from app.extensions import db
from app.models import RefreshToken, User

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/users/me"


def _credentials(email: str = "user@example.com", password: str = "secure-password") -> dict:
    return {"email": email, "password": password}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user_and_returns_token_pair(app, client):
    response = client.post(REGISTER_URL, json=_credentials(" User@Example.com "))

    assert response.status_code == 201
    assert response.json["user"]["email"] == "user@example.com"
    assert response.json["tokens"]["access_token"]
    assert response.json["tokens"]["refresh_token"]
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user is not None
        assert user.password_hash != "secure-password"
        assert db.session.scalar(db.select(RefreshToken)) is not None


def test_duplicate_email_uses_error_contract(client):
    client.post(REGISTER_URL, json=_credentials("User@example.com"))

    response = client.post(REGISTER_URL, json=_credentials("user@example.com"))

    assert response.status_code == 409
    assert response.json["error"] == {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "Пользователь с таким email уже существует",
        "details": {},
    }
    assert response.json["request_id"]


def test_login_rejects_wrong_password(client):
    client.post(REGISTER_URL, json=_credentials())

    response = client.post(LOGIN_URL, json=_credentials(password="wrong-password"))

    assert response.status_code == 401
    assert response.json["error"]["code"] == "INVALID_CREDENTIALS"


def test_access_token_returns_current_user(client):
    registered = client.post(REGISTER_URL, json=_credentials()).json

    response = client.get(ME_URL, headers=_bearer(registered["tokens"]["access_token"]))

    assert response.status_code == 200
    assert response.json["user"]["id"] == registered["user"]["id"]
    assert "password_hash" not in response.json["user"]


def test_refresh_rotates_token_and_revokes_previous_token(client):
    old_refresh = client.post(REGISTER_URL, json=_credentials()).json["tokens"]["refresh_token"]

    refreshed = client.post(REFRESH_URL, headers=_bearer(old_refresh))
    reused = client.post(REFRESH_URL, headers=_bearer(old_refresh))

    assert refreshed.status_code == 200
    assert refreshed.json["tokens"]["refresh_token"] != old_refresh
    assert reused.status_code == 401
    assert reused.json["error"]["code"] == "TOKEN_REVOKED"


def test_logout_revokes_refresh_token(client):
    refresh_token = client.post(REGISTER_URL, json=_credentials()).json["tokens"]["refresh_token"]

    logout = client.post(LOGOUT_URL, headers=_bearer(refresh_token))
    reused = client.post(REFRESH_URL, headers=_bearer(refresh_token))

    assert logout.status_code == 204
    assert reused.status_code == 401
    assert reused.json["error"]["code"] == "TOKEN_REVOKED"


def test_missing_access_token_uses_error_contract(client):
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.json["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json["request_id"]


def test_register_is_rate_limited():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite+pysqlite:///:memory:",
            "JWT_SECRET_KEY": "testing-only-secret-that-is-at-least-32-bytes",
            "RATELIMIT_STORAGE_URI": "memory://",
            "RATELIMIT_ENABLED": True,
        }
    )
    with app.app_context():
        db.create_all()
    client = app.test_client()

    responses = [
        client.post(REGISTER_URL, json=_credentials(f"user{index}@example.com"))
        for index in range(6)
    ]

    assert [response.status_code for response in responses[:5]] == [201] * 5
    assert responses[5].status_code == 429
    assert responses[5].json["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_login_is_rate_limited():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite+pysqlite:///:memory:",
            "JWT_SECRET_KEY": "testing-only-secret-that-is-at-least-32-bytes",
            "RATELIMIT_STORAGE_URI": "memory://",
            "RATELIMIT_ENABLED": True,
        }
    )
    with app.app_context():
        db.create_all()
    client = app.test_client()

    responses = [
        client.post(LOGIN_URL, json=_credentials(password="wrong-password")) for _index in range(11)
    ]

    assert [response.status_code for response in responses[:10]] == [401] * 10
    assert responses[10].status_code == 429
    assert responses[10].json["error"]["code"] == "RATE_LIMIT_EXCEEDED"

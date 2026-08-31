import uuid

import pytest


@pytest.fixture()
def auth_client(client):
    def authenticate(email: str = "user@example.com") -> dict:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "secure-password"},
        )
        assert response.status_code == 201
        return {
            "user": response.json["user"],
            "headers": {"Authorization": f"Bearer {response.json['tokens']['access_token']}"},
        }

    return authenticate


@pytest.fixture()
def expense_payload():
    def build(category_id: str, **overrides) -> dict:
        payload = {
            "category_id": category_id,
            "amount": "1250.50",
            "currency": "RUB",
            "expense_date": "2026-08-31",
            "merchant": "Кофейня",
            "description": "Обед",
            "comment": "Встреча",
            "source": "MANUAL",
            "client_operation_id": str(uuid.uuid4()),
        }
        payload.update(overrides)
        return payload

    return build

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.auth.service import AuthService
from app.extensions import db
from app.models import Expense, Subscription, SubscriptionPayment
from app.subscriptions.service import SubscriptionService


def _category_id(client, headers):
    return client.get("/api/v1/categories", headers=headers).json["items"][0]["id"]


def _payload(category_id, **overrides):
    payload = {
        "name": "Музыка",
        "category_id": category_id,
        "amount": "299.00",
        "currency": "RUB",
        "frequency": "MONTHLY",
        "next_payment_date": "2026-01-31",
        "comment": "Семейный тариф",
    }
    payload.update(overrides)
    return payload


def test_subscription_crud(client, auth_client):
    auth = auth_client()
    created = client.post(
        "/api/v1/subscriptions",
        json=_payload(_category_id(client, auth["headers"])),
        headers=auth["headers"],
    )
    subscription_id = created.json["subscription"]["id"]
    fetched = client.get(f"/api/v1/subscriptions/{subscription_id}", headers=auth["headers"])
    updated = client.patch(
        f"/api/v1/subscriptions/{subscription_id}",
        json={"amount": "399.00", "is_active": False},
        headers=auth["headers"],
    )
    deleted = client.delete(f"/api/v1/subscriptions/{subscription_id}", headers=auth["headers"])

    assert created.status_code == 201
    assert fetched.status_code == 200
    assert updated.json["subscription"]["amount"] == "399.00"
    assert deleted.status_code == 204
    assert (
        client.get(f"/api/v1/subscriptions/{subscription_id}", headers=auth["headers"]).status_code
        == 404
    )


def test_payment_is_atomic_and_idempotent(app, client, auth_client):
    auth = auth_client()
    subscription = client.post(
        "/api/v1/subscriptions",
        json=_payload(_category_id(client, auth["headers"])),
        headers=auth["headers"],
    ).json["subscription"]
    operation_id = str(uuid.uuid4())
    payload = {"client_operation_id": operation_id, "payment_date": "2026-01-31"}

    first = client.post(
        f"/api/v1/subscriptions/{subscription['id']}/payments",
        json=payload,
        headers=auth["headers"],
    )
    repeated = client.post(
        f"/api/v1/subscriptions/{subscription['id']}/payments",
        json=payload,
        headers=auth["headers"],
    )
    history = client.get(
        f"/api/v1/subscriptions/{subscription['id']}/payments", headers=auth["headers"]
    )

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.json["payment"]["id"] == first.json["payment"]["id"]
    assert first.json["subscription"]["next_payment_date"] == "2026-02-28"
    assert len(history.json["items"]) == 1
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Expense)) == 1
        assert db.session.scalar(db.select(db.func.count()).select_from(SubscriptionPayment)) == 1
        expense = db.session.scalar(db.select(Expense))
        assert expense.source == "SUBSCRIPTION"
        assert expense.amount == Decimal("299.00")


def test_payment_rolls_back_all_steps_on_failure(app, client, auth_client):
    auth = auth_client()
    subscription_id = client.post(
        "/api/v1/subscriptions",
        json=_payload(_category_id(client, auth["headers"])),
        headers=auth["headers"],
    ).json["subscription"]["id"]
    with app.app_context():
        user = AuthService().get_user(auth["user"]["id"])
        service = SubscriptionService(
            calculator=lambda *_args: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        with pytest.raises(RuntimeError):
            service.pay(uuid.UUID(subscription_id), uuid.uuid4(), date(2026, 1, 31), user)
        assert db.session.scalar(db.select(db.func.count()).select_from(Expense)) == 0
        assert db.session.scalar(db.select(db.func.count()).select_from(SubscriptionPayment)) == 0
        subscription = db.session.scalar(db.select(Subscription))
        assert subscription.next_payment_date == date(2026, 1, 31)


def test_user_cannot_access_or_pay_another_users_subscription(client, auth_client):
    user_a = auth_client("a@example.com")
    subscription_id = client.post(
        "/api/v1/subscriptions",
        json=_payload(_category_id(client, user_a["headers"])),
        headers=user_a["headers"],
    ).json["subscription"]["id"]
    user_b = auth_client("b@example.com")

    assert (
        client.get(
            f"/api/v1/subscriptions/{subscription_id}", headers=user_b["headers"]
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/subscriptions/{subscription_id}",
            json={"amount": "1.00"},
            headers=user_b["headers"],
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/subscriptions/{subscription_id}", headers=user_b["headers"]
        ).status_code
        == 404
    )
    payment = client.post(
        f"/api/v1/subscriptions/{subscription_id}/payments",
        json={"client_operation_id": str(uuid.uuid4())},
        headers=user_b["headers"],
    )
    assert payment.status_code == 404

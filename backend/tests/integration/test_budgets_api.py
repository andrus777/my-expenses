import uuid

from sqlalchemy import func, select

from app.extensions import db
from app.models import BudgetThresholdEvent


def _category(client, headers):
    response = client.get("/api/v1/categories", headers=headers)
    return response.json["items"][0]["id"]


def _budget_payload(category_id, **overrides):
    payload = {
        "category_id": category_id,
        "amount": "1000.00",
        "currency": "RUB",
        "period": "MONTH",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
    }
    payload.update(overrides)
    return payload


def _expense(client, headers, category_id, amount, operation_id=None):
    response = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": category_id,
            "amount": amount,
            "currency": "RUB",
            "expense_date": "2026-09-15",
            "source": "MANUAL",
            "client_operation_id": operation_id or str(uuid.uuid4()),
        },
    )
    assert response.status_code == 201
    return response.json["expense"]


def test_budget_crud_and_calculated_fields(client, auth_client):
    auth = auth_client()
    category_id = _category(client, auth["headers"])
    created = client.post(
        "/api/v1/budgets", headers=auth["headers"], json=_budget_payload(category_id)
    )
    assert created.status_code == 201
    budget_id = created.json["budget"]["id"]
    _expense(client, auth["headers"], category_id, "250.00")

    fetched = client.get(f"/api/v1/budgets/{budget_id}", headers=auth["headers"])
    assert fetched.json["budget"]["spent"] == "250.00"
    assert fetched.json["budget"]["remaining"] == "750.00"
    assert fetched.json["budget"]["usage_percent"] == "25.00"

    updated = client.patch(
        f"/api/v1/budgets/{budget_id}", headers=auth["headers"], json={"amount": "500.00"}
    )
    assert updated.status_code == 200
    assert updated.json["budget"]["usage_percent"] == "50.00"
    assert client.delete(f"/api/v1/budgets/{budget_id}", headers=auth["headers"]).status_code == 204
    assert client.get(f"/api/v1/budgets/{budget_id}", headers=auth["headers"]).status_code == 404


def test_soft_deleted_expenses_are_excluded(client, auth_client):
    auth = auth_client()
    category_id = _category(client, auth["headers"])
    budget = client.post(
        "/api/v1/budgets", headers=auth["headers"], json=_budget_payload(category_id)
    ).json["budget"]
    expense = _expense(client, auth["headers"], category_id, "900.00")
    assert (
        client.delete(f"/api/v1/expenses/{expense['id']}", headers=auth["headers"]).status_code
        == 204
    )

    fetched = client.get(f"/api/v1/budgets/{budget['id']}", headers=auth["headers"])
    assert fetched.json["budget"]["spent"] == "0.00"
    assert fetched.json["budget"]["thresholds_reached"] == []


def test_threshold_events_are_not_duplicated(client, auth_client, app):
    auth = auth_client()
    category_id = _category(client, auth["headers"])
    budget_id = client.post(
        "/api/v1/budgets", headers=auth["headers"], json=_budget_payload(category_id)
    ).json["budget"]["id"]
    _expense(client, auth["headers"], category_id, "1000.00")

    first = client.get(f"/api/v1/budgets/{budget_id}", headers=auth["headers"])
    second = client.get(f"/api/v1/budgets/{budget_id}", headers=auth["headers"])

    assert first.json["budget"]["thresholds_reached"] == [80, 100]
    assert second.json["budget"]["thresholds_reached"] == [80, 100]
    with app.app_context():
        assert db.session.scalar(select(func.count(BudgetThresholdEvent.id))) == 2


def test_other_users_budget_is_hidden_for_all_object_operations(client, auth_client):
    owner = auth_client("budget-owner@example.com")
    stranger = auth_client("budget-stranger@example.com")
    budget_id = client.post(
        "/api/v1/budgets",
        headers=owner["headers"],
        json=_budget_payload(_category(client, owner["headers"])),
    ).json["budget"]["id"]

    assert (
        client.get(f"/api/v1/budgets/{budget_id}", headers=stranger["headers"]).status_code == 404
    )
    assert (
        client.patch(
            f"/api/v1/budgets/{budget_id}", headers=stranger["headers"], json={"amount": "1.00"}
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/budgets/{budget_id}", headers=stranger["headers"]).status_code
        == 404
    )
    assert client.get("/api/v1/budgets", headers=stranger["headers"]).json["items"] == []

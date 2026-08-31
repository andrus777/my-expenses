from decimal import Decimal

from app.extensions import db
from app.models import Expense


def _system_category_id(client, headers) -> str:
    categories = client.get("/api/v1/categories", headers=headers).json["items"]
    return next(category["id"] for category in categories if category["is_system"])


def test_expense_crud_and_soft_delete(app, client, auth_client, expense_payload):
    auth = auth_client()
    category_id = _system_category_id(client, auth["headers"])
    created = client.post(
        "/api/v1/expenses", json=expense_payload(category_id), headers=auth["headers"]
    )
    expense_id = created.json["expense"]["id"]

    fetched = client.get(f"/api/v1/expenses/{expense_id}", headers=auth["headers"])
    updated = client.patch(
        f"/api/v1/expenses/{expense_id}",
        json={"amount": "999.99", "merchant": "Новая кофейня"},
        headers=auth["headers"],
    )
    deleted = client.delete(f"/api/v1/expenses/{expense_id}", headers=auth["headers"])
    missing = client.get(f"/api/v1/expenses/{expense_id}", headers=auth["headers"])
    listed = client.get("/api/v1/expenses", headers=auth["headers"])

    assert created.status_code == 201
    assert created.json["expense"]["amount"] == "1250.50"
    assert fetched.status_code == 200
    assert updated.json["expense"]["amount"] == "999.99"
    assert deleted.status_code == 204
    assert missing.status_code == 404
    assert listed.json["items"] == []
    with app.app_context():
        expense = db.session.scalar(db.select(Expense))
        assert expense is not None
        assert expense.deleted_at is not None
        assert expense.amount == Decimal("999.99")


def test_expense_create_is_idempotent(client, auth_client, expense_payload):
    auth = auth_client()
    payload = expense_payload(_system_category_id(client, auth["headers"]))

    first = client.post("/api/v1/expenses", json=payload, headers=auth["headers"])
    repeated = client.post("/api/v1/expenses", json=payload, headers=auth["headers"])
    conflict = client.post(
        "/api/v1/expenses",
        json={**payload, "amount": "10.00"},
        headers=auth["headers"],
    )

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.json["expense"]["id"] == first.json["expense"]["id"]
    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "CLIENT_OPERATION_CONFLICT"


def test_amount_must_be_positive_decimal_string(client, auth_client, expense_payload):
    auth = auth_client()
    category_id = _system_category_id(client, auth["headers"])

    negative = client.post(
        "/api/v1/expenses",
        json=expense_payload(category_id, amount="-1.00"),
        headers=auth["headers"],
    )
    floating = client.post(
        "/api/v1/expenses",
        json=expense_payload(category_id, amount=10.5),
        headers=auth["headers"],
    )

    assert negative.status_code == 400
    assert floating.status_code == 400


def test_category_in_use_cannot_be_deleted(client, auth_client, expense_payload):
    auth = auth_client()
    category = client.post(
        "/api/v1/categories", json={"name": "Работа"}, headers=auth["headers"]
    ).json["category"]
    client.post("/api/v1/expenses", json=expense_payload(category["id"]), headers=auth["headers"])

    response = client.delete(f"/api/v1/categories/{category['id']}", headers=auth["headers"])

    assert response.status_code == 409
    assert response.json["error"]["code"] == "CATEGORY_IN_USE"


def test_expense_pagination_filters_search_and_sort(client, auth_client, expense_payload):
    auth = auth_client()
    category_id = _system_category_id(client, auth["headers"])
    records = (
        ("10.00", "2026-08-01", "Аптека", "Здоровье"),
        ("30.00", "2026-08-03", "Кафе", "Обед"),
        ("20.00", "2026-08-02", "Кафе", "Завтрак"),
    )
    for amount, expense_date, merchant, description in records:
        client.post(
            "/api/v1/expenses",
            json=expense_payload(
                category_id,
                amount=amount,
                expense_date=expense_date,
                merchant=merchant,
                description=description,
            ),
            headers=auth["headers"],
        )

    page = client.get(
        "/api/v1/expenses?search=Кафе&min_amount=15.00&sort=amount&order=asc&page=1&per_page=1",
        headers=auth["headers"],
    )
    date_filtered = client.get(
        "/api/v1/expenses?date_from=2026-08-02&date_to=2026-08-03",
        headers=auth["headers"],
    )

    assert page.status_code == 200
    assert [item["amount"] for item in page.json["items"]] == ["20.00"]
    assert page.json["pagination"] == {"page": 1, "per_page": 1, "total": 2, "pages": 2}
    assert date_filtered.json["pagination"]["total"] == 2


def test_expense_filters_by_category_currency_and_source(client, auth_client, expense_payload):
    auth = auth_client()
    system_category_id = _system_category_id(client, auth["headers"])
    custom_category_id = client.post(
        "/api/v1/categories", json={"name": "Поездки"}, headers=auth["headers"]
    ).json["category"]["id"]
    client.post(
        "/api/v1/expenses",
        json=expense_payload(system_category_id, amount="10.00"),
        headers=auth["headers"],
    )
    expected = client.post(
        "/api/v1/expenses",
        json=expense_payload(custom_category_id, amount="50.00", currency="USD", source="SYNC"),
        headers=auth["headers"],
    ).json["expense"]

    response = client.get(
        f"/api/v1/expenses?category_id={custom_category_id}&currency=usd&source=sync",
        headers=auth["headers"],
    )

    assert [item["id"] for item in response.json["items"]] == [expected["id"]]


def test_security_user_cannot_access_another_users_expense(client, auth_client, expense_payload):
    user_a = auth_client("a@example.com")
    category_a = client.post(
        "/api/v1/categories", json={"name": "Секрет A"}, headers=user_a["headers"]
    ).json["category"]
    created = client.post(
        "/api/v1/expenses",
        json=expense_payload(category_a["id"]),
        headers=user_a["headers"],
    ).json["expense"]
    user_b = auth_client("b@example.com")

    fetched = client.get(f"/api/v1/expenses/{created['id']}", headers=user_b["headers"])
    updated = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"amount": "1.00"},
        headers=user_b["headers"],
    )
    deleted = client.delete(f"/api/v1/expenses/{created['id']}", headers=user_b["headers"])
    listed = client.get("/api/v1/expenses", headers=user_b["headers"])
    category_reuse = client.post(
        "/api/v1/expenses",
        json=expense_payload(category_a["id"]),
        headers=user_b["headers"],
    )

    assert fetched.status_code == 404
    assert updated.status_code == 404
    assert deleted.status_code == 404
    assert listed.json["items"] == []
    assert category_reuse.status_code == 404
    assert (
        client.get(f"/api/v1/expenses/{created['id']}", headers=user_a["headers"]).status_code
        == 200
    )

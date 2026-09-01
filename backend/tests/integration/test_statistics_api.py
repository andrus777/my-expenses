import uuid


def _category(client, headers):
    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    return response.json["items"][0]["id"]


def _expense(client, headers, category_id, amount, expense_date):
    response = client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "category_id": category_id,
            "amount": amount,
            "currency": "RUB",
            "expense_date": expense_date,
            "source": "MANUAL",
            "client_operation_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 201


def test_summary_uses_inclusive_boundaries_and_equal_previous_period(client, auth_client):
    auth = auth_client()
    category_id = _category(client, auth["headers"])
    _expense(client, auth["headers"], category_id, "40.00", "2026-01-01")
    _expense(client, auth["headers"], category_id, "60.00", "2026-01-07")
    _expense(client, auth["headers"], category_id, "50.00", "2025-12-31")
    _expense(client, auth["headers"], category_id, "999.00", "2026-01-08")

    response = client.get(
        "/api/v1/statistics/summary?date_from=2026-01-01&date_to=2026-01-07",
        headers=auth["headers"],
    )

    assert response.status_code == 200
    assert response.json == {
        "date_from": "2026-01-01",
        "date_to": "2026-01-07",
        "currency": "RUB",
        "total": "100.00",
        "operations_count": 2,
        "average_daily": "14.29",
        "previous_period_total": "50.00",
        "change_percent": "100.00",
    }


def test_empty_period_returns_deterministic_zeroes_and_complete_timeline(client, auth_client):
    auth = auth_client()
    summary = client.get(
        "/api/v1/statistics/summary?date_from=2024-02-28&date_to=2024-03-01",
        headers=auth["headers"],
    )
    timeline = client.get(
        "/api/v1/statistics/timeline?date_from=2024-02-28&date_to=2024-03-01&interval=day",
        headers=auth["headers"],
    )

    assert summary.status_code == 200
    assert summary.json["total"] == "0.00"
    assert summary.json["average_daily"] == "0.00"
    assert summary.json["change_percent"] is None
    assert timeline.json["items"] == [
        {"period": "2024-02-28", "total": "0.00", "operations_count": 0},
        {"period": "2024-02-29", "total": "0.00", "operations_count": 0},
        {"period": "2024-03-01", "total": "0.00", "operations_count": 0},
    ]


def test_categories_timeline_and_user_isolation(client, auth_client):
    first = auth_client("statistics-a@example.com")
    second = auth_client("statistics-b@example.com")
    first_category = _category(client, first["headers"])
    second_category = _category(client, second["headers"])
    _expense(client, first["headers"], first_category, "25.00", "2026-08-31")
    _expense(client, second["headers"], second_category, "900.00", "2026-08-31")

    query = "?date_from=2026-08-31&date_to=2026-09-01"
    categories = client.get("/api/v1/statistics/categories" + query, headers=first["headers"])
    timeline = client.get(
        "/api/v1/statistics/timeline" + query + "&interval=day", headers=first["headers"]
    )

    assert categories.json["items"][0]["total"] == "25.00"
    assert categories.json["items"][0]["percent"] == "100.00"
    assert timeline.json["items"] == [
        {"period": "2026-08-31", "total": "25.00", "operations_count": 1},
        {"period": "2026-09-01", "total": "0.00", "operations_count": 0},
    ]


def test_subscription_projection_and_validation(client, auth_client):
    auth = auth_client()
    category_id = _category(client, auth["headers"])
    for name, amount, frequency in [
        ("Monthly", "100.00", "MONTHLY"),
        ("Yearly", "1200.00", "YEARLY"),
    ]:
        response = client.post(
            "/api/v1/subscriptions",
            headers=auth["headers"],
            json={
                "name": name,
                "category_id": category_id,
                "amount": amount,
                "currency": "RUB",
                "frequency": frequency,
                "next_payment_date": "2026-09-01",
            },
        )
        assert response.status_code == 201

    totals = client.get("/api/v1/statistics/subscriptions", headers=auth["headers"])
    invalid = client.get(
        "/api/v1/statistics/timeline?date_from=2026-09-02&date_to=2026-09-01",
        headers=auth["headers"],
    )

    assert totals.json == {
        "currency": "RUB",
        "monthly_total": "200.00",
        "yearly_total": "2400.00",
        "active_count": 2,
    }
    assert invalid.status_code == 400
    assert invalid.json["error"]["code"] == "VALIDATION_ERROR"

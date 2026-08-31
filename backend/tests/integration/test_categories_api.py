def _system_categories(client, headers):
    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    return [category for category in response.json["items"] if category["is_system"]]


def test_system_categories_are_seeded_and_visible(client, auth_client):
    auth = auth_client()

    categories = _system_categories(client, auth["headers"])

    assert len(categories) == 8
    assert "Продукты" in {category["name"] for category in categories}


def test_user_category_crud(client, auth_client):
    auth = auth_client()

    created = client.post("/api/v1/categories", json={"name": "Питомцы"}, headers=auth["headers"])
    category_id = created.json["category"]["id"]
    fetched = client.get(f"/api/v1/categories/{category_id}", headers=auth["headers"])
    updated = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Домашние животные"},
        headers=auth["headers"],
    )
    deleted = client.delete(f"/api/v1/categories/{category_id}", headers=auth["headers"])
    missing = client.get(f"/api/v1/categories/{category_id}", headers=auth["headers"])

    assert created.status_code == 201
    assert not created.json["category"]["is_system"]
    assert fetched.status_code == 200
    assert updated.json["category"]["name"] == "Домашние животные"
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_duplicate_user_category_is_rejected_case_insensitively(client, auth_client):
    auth = auth_client()
    client.post("/api/v1/categories", json={"name": "Питомцы"}, headers=auth["headers"])

    response = client.post("/api/v1/categories", json={"name": "питомцы"}, headers=auth["headers"])

    assert response.status_code == 409
    assert response.json["error"]["code"] == "CATEGORY_ALREADY_EXISTS"


def test_system_category_cannot_be_modified_or_deleted(client, auth_client):
    auth = auth_client()
    category_id = _system_categories(client, auth["headers"])[0]["id"]

    updated = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Изменено"},
        headers=auth["headers"],
    )
    deleted = client.delete(f"/api/v1/categories/{category_id}", headers=auth["headers"])

    assert updated.status_code == 403
    assert updated.json["error"]["code"] == "SYSTEM_CATEGORY_IMMUTABLE"
    assert deleted.status_code == 403


def test_other_users_category_is_hidden(client, auth_client):
    user_a = auth_client("a@example.com")
    created = client.post(
        "/api/v1/categories", json={"name": "Личное A"}, headers=user_a["headers"]
    )
    category_id = created.json["category"]["id"]
    user_b = auth_client("b@example.com")

    fetched = client.get(f"/api/v1/categories/{category_id}", headers=user_b["headers"])
    updated = client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Взлом"},
        headers=user_b["headers"],
    )
    deleted = client.delete(f"/api/v1/categories/{category_id}", headers=user_b["headers"])
    visible_ids = {
        category["id"]
        for category in client.get("/api/v1/categories", headers=user_b["headers"]).json["items"]
    }

    assert fetched.status_code == 404
    assert updated.status_code == 404
    assert deleted.status_code == 404
    assert category_id not in visible_ids

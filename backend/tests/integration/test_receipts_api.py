import uuid

from app.extensions import db
from app.models import Expense, Receipt, ReceiptJob


def _category_id(client, headers):
    return client.get("/api/v1/categories", headers=headers).json["items"][0]["id"]


def _create_completed_job(client, headers):
    created = client.post(
        "/api/v1/receipts", json={"receipt_data": "fake-fiscal-qr"}, headers=headers
    )
    assert created.status_code == 202
    job = client.get(f"/api/v1/receipts/jobs/{created.json['job_id']}", headers=headers)
    assert job.status_code == 200
    assert job.json["status"] == "COMPLETED"
    return created, job.json


def test_job_runs_with_fake_provider_and_returns_preview(app, client, auth_client):
    auth = auth_client()

    created, job = _create_completed_job(client, auth["headers"])

    assert created.json["status"] == "PENDING"
    assert job["attempts"] == 1
    assert job["receipt"]["merchant"] == "Тестовый магазин"
    assert job["receipt"]["total"] == "350.00"
    assert len(job["receipt"]["items"]) == 2
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(ReceiptJob)) == 1
        assert db.session.scalar(db.select(db.func.count()).select_from(Receipt)) == 1


def test_finalize_is_idempotent_and_creates_one_expense(app, client, auth_client):
    auth = auth_client()
    _, job = _create_completed_job(client, auth["headers"])
    operation_id = str(uuid.uuid4())
    payload = {
        "category_id": _category_id(client, auth["headers"]),
        "client_operation_id": operation_id,
    }
    url = f"/api/v1/receipts/{job['receipt']['id']}/finalize"

    first = client.post(url, json=payload, headers=auth["headers"])
    repeated = client.post(url, json=payload, headers=auth["headers"])
    conflict = client.post(
        url,
        json={**payload, "client_operation_id": str(uuid.uuid4())},
        headers=auth["headers"],
    )

    assert first.status_code == 201
    assert repeated.status_code == 200
    assert repeated.json["expense"]["id"] == first.json["expense"]["id"]
    assert first.json["expense"]["source"] == "RECEIPT"
    assert conflict.status_code == 409
    assert conflict.json["error"]["code"] == "RECEIPT_ALREADY_FINALIZED"
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(Expense)) == 1


def test_user_cannot_read_or_finalize_another_users_receipt(client, auth_client):
    user_a = auth_client("receipt-a@example.com")
    created, job = _create_completed_job(client, user_a["headers"])
    user_b = auth_client("receipt-b@example.com")

    hidden_job = client.get(
        f"/api/v1/receipts/jobs/{created.json['job_id']}", headers=user_b["headers"]
    )
    finalize = client.post(
        f"/api/v1/receipts/{job['receipt']['id']}/finalize",
        json={
            "category_id": _category_id(client, user_b["headers"]),
            "client_operation_id": str(uuid.uuid4()),
        },
        headers=user_b["headers"],
    )

    assert hidden_job.status_code == 404
    assert finalize.status_code == 404

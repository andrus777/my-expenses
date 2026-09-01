from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.api.errors import ApiError
from app.auth.service import AuthService
from app.receipts.providers import get_receipt_provider
from app.receipts.service import ReceiptService
from app.receipts.tasks import process_receipt_job
from app.schemas.common import parse_uuid

blueprint = Blueprint("receipts", __name__, url_prefix="/receipts")


def _current_user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.post("")
@jwt_required()
def create_receipt_job():  # type: ignore[no-untyped-def]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("receipt_data"), str):
        raise ApiError("VALIDATION_ERROR", "Передайте receipt_data", 400)
    job = ReceiptService().create_job(payload["receipt_data"], _current_user())
    response = {"job_id": str(job.public_id), "status": "PENDING"}
    if current_app.testing:
        provider = get_receipt_provider()
        ReceiptService().process(job.public_id, provider, current_app.config["RECEIPT_PROVIDER"])
    else:
        process_receipt_job.delay(str(job.public_id))
    return jsonify(response), 202


@blueprint.get("/jobs/<job_id>")
@jwt_required()
def get_receipt_job(job_id: str):  # type: ignore[no-untyped-def]
    job = ReceiptService().get_job(parse_uuid(job_id, "job_id"), _current_user())
    return jsonify(job.to_dict())


@blueprint.post("/<receipt_id>/finalize")
@jwt_required()
def finalize_receipt(receipt_id: str):  # type: ignore[no-untyped-def]
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    missing = {"category_id", "client_operation_id"} - set(payload)
    if missing:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {field: ["Обязательное поле"] for field in sorted(missing)},
        )
    expense, created = ReceiptService().finalize(
        parse_uuid(receipt_id, "receipt_id"),
        parse_uuid(payload["category_id"], "category_id"),
        parse_uuid(payload["client_operation_id"], "client_operation_id"),
        _current_user(),
    )
    return jsonify({"expense": expense.to_dict()}), 201 if created else 200

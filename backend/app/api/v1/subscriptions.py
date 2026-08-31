from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.service import AuthService
from app.schemas.common import parse_uuid
from app.schemas.subscriptions import parse_payment, parse_subscription
from app.subscriptions.service import SubscriptionService

blueprint = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")


def _current_user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.get("")
@jwt_required()
def list_subscriptions():  # type: ignore[no-untyped-def]
    return jsonify(
        {"items": [item.to_dict() for item in SubscriptionService().list(_current_user())]}
    )


@blueprint.post("")
@jwt_required()
def create_subscription():  # type: ignore[no-untyped-def]
    item = SubscriptionService().create(
        parse_subscription(request.get_json(silent=True)), _current_user()
    )
    return jsonify({"subscription": item.to_dict()}), 201


@blueprint.get("/<subscription_id>")
@jwt_required()
def get_subscription(subscription_id: str):  # type: ignore[no-untyped-def]
    item = SubscriptionService().get(
        parse_uuid(subscription_id, "subscription_id"), _current_user()
    )
    return jsonify({"subscription": item.to_dict()})


@blueprint.patch("/<subscription_id>")
@jwt_required()
def update_subscription(subscription_id: str):  # type: ignore[no-untyped-def]
    item = SubscriptionService().update(
        parse_uuid(subscription_id, "subscription_id"),
        parse_subscription(request.get_json(silent=True), partial=True),
        _current_user(),
    )
    return jsonify({"subscription": item.to_dict()})


@blueprint.delete("/<subscription_id>")
@jwt_required()
def delete_subscription(subscription_id: str):  # type: ignore[no-untyped-def]
    SubscriptionService().delete(parse_uuid(subscription_id, "subscription_id"), _current_user())
    return "", 204


@blueprint.get("/<subscription_id>/payments")
@jwt_required()
def list_payments(subscription_id: str):  # type: ignore[no-untyped-def]
    items = SubscriptionService().payments(
        parse_uuid(subscription_id, "subscription_id"), _current_user()
    )
    return jsonify({"items": [item.to_dict() for item in items]})


@blueprint.post("/<subscription_id>/payments")
@jwt_required()
def create_payment(subscription_id: str):  # type: ignore[no-untyped-def]
    operation_id, payment_date = parse_payment(request.get_json(silent=True))
    payment, created = SubscriptionService().pay(
        parse_uuid(subscription_id, "subscription_id"), operation_id, payment_date, _current_user()
    )
    return jsonify(
        {"payment": payment.to_dict(), "subscription": payment.subscription.to_dict()}
    ), 201 if created else 200

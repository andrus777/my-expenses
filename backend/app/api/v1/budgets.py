from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.service import AuthService
from app.budgets.service import BudgetService
from app.schemas.budgets import parse_budget
from app.schemas.common import parse_uuid

blueprint = Blueprint("budgets", __name__, url_prefix="/budgets")


def _user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.get("")
@jwt_required()
def list_budgets():  # type: ignore[no-untyped-def]
    return jsonify({"items": BudgetService().list(_user())})


@blueprint.post("")
@jwt_required()
def create_budget():  # type: ignore[no-untyped-def]
    return jsonify(
        {"budget": BudgetService().create(parse_budget(request.get_json(silent=True)), _user())}
    ), 201


@blueprint.get("/<budget_id>")
@jwt_required()
def get_budget(budget_id: str):  # type: ignore[no-untyped-def]
    return jsonify(
        {"budget": BudgetService().get_result(parse_uuid(budget_id, "budget_id"), _user())}
    )


@blueprint.patch("/<budget_id>")
@jwt_required()
def update_budget(budget_id: str):  # type: ignore[no-untyped-def]
    return jsonify(
        {
            "budget": BudgetService().update(
                parse_uuid(budget_id, "budget_id"),
                parse_budget(request.get_json(silent=True), partial=True),
                _user(),
            )
        }
    )


@blueprint.delete("/<budget_id>")
@jwt_required()
def delete_budget(budget_id: str):  # type: ignore[no-untyped-def]
    BudgetService().delete(parse_uuid(budget_id, "budget_id"), _user())
    return "", 204

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.service import AuthService
from app.expenses.service import ExpenseService
from app.schemas.common import parse_uuid
from app.schemas.expense_filters import parse_expense_filters
from app.schemas.expenses import parse_expense_create, parse_expense_patch

blueprint = Blueprint("expenses", __name__, url_prefix="/expenses")


def _current_user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.get("")
@jwt_required()
def list_expenses():  # type: ignore[no-untyped-def]
    expenses, pagination = ExpenseService().list(_current_user(), parse_expense_filters(request))
    return jsonify({"items": [expense.to_dict() for expense in expenses], "pagination": pagination})


@blueprint.post("")
@jwt_required()
def create_expense():  # type: ignore[no-untyped-def]
    expense, created = ExpenseService().create(
        parse_expense_create(request.get_json(silent=True)), _current_user()
    )
    return jsonify({"expense": expense.to_dict()}), 201 if created else 200


@blueprint.get("/<expense_id>")
@jwt_required()
def get_expense(expense_id: str):  # type: ignore[no-untyped-def]
    expense = ExpenseService().get(parse_uuid(expense_id, "expense_id"), _current_user())
    return jsonify({"expense": expense.to_dict()})


@blueprint.patch("/<expense_id>")
@jwt_required()
def update_expense(expense_id: str):  # type: ignore[no-untyped-def]
    expense = ExpenseService().update(
        parse_uuid(expense_id, "expense_id"),
        parse_expense_patch(request.get_json(silent=True)),
        _current_user(),
    )
    return jsonify({"expense": expense.to_dict()})


@blueprint.delete("/<expense_id>")
@jwt_required()
def delete_expense(expense_id: str):  # type: ignore[no-untyped-def]
    ExpenseService().delete(parse_uuid(expense_id, "expense_id"), _current_user())
    return "", 204

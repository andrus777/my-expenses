from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.service import AuthService
from app.categories.service import CategoryService
from app.schemas.categories import parse_category_payload
from app.schemas.common import parse_uuid

blueprint = Blueprint("categories", __name__, url_prefix="/categories")


def _current_user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.get("")
@jwt_required()
def list_categories():  # type: ignore[no-untyped-def]
    categories = CategoryService().list(_current_user())
    return jsonify({"items": [category.to_dict() for category in categories]})


@blueprint.post("")
@jwt_required()
def create_category():  # type: ignore[no-untyped-def]
    name = parse_category_payload(request.get_json(silent=True))
    category = CategoryService().create(name, _current_user())
    return jsonify({"category": category.to_dict()}), 201


@blueprint.get("/<category_id>")
@jwt_required()
def get_category(category_id: str):  # type: ignore[no-untyped-def]
    category = CategoryService().get(parse_uuid(category_id, "category_id"), _current_user())
    return jsonify({"category": category.to_dict()})


@blueprint.patch("/<category_id>")
@jwt_required()
def update_category(category_id: str):  # type: ignore[no-untyped-def]
    name = parse_category_payload(request.get_json(silent=True))
    category = CategoryService().update(
        parse_uuid(category_id, "category_id"), name, _current_user()
    )
    return jsonify({"category": category.to_dict()})


@blueprint.delete("/<category_id>")
@jwt_required()
def delete_category(category_id: str):  # type: ignore[no-untyped-def]
    CategoryService().delete(parse_uuid(category_id, "category_id"), _current_user())
    return "", 204

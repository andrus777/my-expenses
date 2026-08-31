from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.auth.service import AuthService

blueprint = Blueprint("users", __name__, url_prefix="/users")


@blueprint.get("/me")
@jwt_required()
def me():  # type: ignore[no-untyped-def]
    user = AuthService().get_user(get_jwt_identity())
    return jsonify({"user": user.to_dict()})

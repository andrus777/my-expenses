from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.auth.service import AuthService, TokenPair
from app.extensions import limiter
from app.schemas.auth import parse_credentials

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


def _tokens_response(tokens: TokenPair) -> dict[str, str]:
    return {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}


@blueprint.post("/register")
@limiter.limit("5 per minute")
def register():  # type: ignore[no-untyped-def]
    credentials = parse_credentials(request.get_json(silent=True), validate_password_length=True)
    user, tokens = AuthService().register(credentials)
    return jsonify({"user": user.to_dict(), "tokens": _tokens_response(tokens)}), 201


@blueprint.post("/login")
@limiter.limit("10 per minute")
def login():  # type: ignore[no-untyped-def]
    credentials = parse_credentials(request.get_json(silent=True), validate_password_length=False)
    user, tokens = AuthService().login(credentials)
    return jsonify({"user": user.to_dict(), "tokens": _tokens_response(tokens)})


@blueprint.post("/refresh")
@jwt_required(refresh=True)
def refresh():  # type: ignore[no-untyped-def]
    service = AuthService()
    user = service.get_user(get_jwt_identity())
    tokens = service.refresh(user, get_jwt()["jti"])
    return jsonify({"tokens": _tokens_response(tokens)})


@blueprint.post("/logout")
@jwt_required(refresh=True)
def logout():  # type: ignore[no-untyped-def]
    AuthService().logout(get_jwt()["jti"])
    return "", 204

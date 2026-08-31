from flask_jwt_extended import JWTManager

from app.api.errors import error_response
from app.repositories.refresh_tokens import RefreshTokenRepository


def register_jwt_callbacks(jwt: JWTManager) -> None:
    @jwt.token_in_blocklist_loader
    def token_in_blocklist(_header: dict, payload: dict) -> bool:
        if payload.get("type") != "refresh":
            return False
        return RefreshTokenRepository().is_revoked_or_unknown(payload["jti"])

    @jwt.revoked_token_loader
    def revoked_token(_header: dict, _payload: dict):  # type: ignore[no-untyped-def]
        return error_response("TOKEN_REVOKED", "Refresh token отозван", 401)

    @jwt.expired_token_loader
    def expired_token(_header: dict, _payload: dict):  # type: ignore[no-untyped-def]
        return error_response("TOKEN_EXPIRED", "Срок действия токена истёк", 401)

    @jwt.invalid_token_loader
    def invalid_token(_reason: str):  # type: ignore[no-untyped-def]
        return error_response("TOKEN_INVALID", "Недействительный токен", 401)

    @jwt.unauthorized_loader
    def missing_token(_reason: str):  # type: ignore[no-untyped-def]
        return error_response("AUTHENTICATION_REQUIRED", "Требуется авторизация", 401)

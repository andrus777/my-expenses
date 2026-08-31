from dataclasses import dataclass
from datetime import UTC, datetime

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.auth.passwords import hash_password, verify_password
from app.extensions import db
from app.models import RefreshToken, User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import Credentials


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.refresh_tokens = RefreshTokenRepository()

    def register(self, credentials: Credentials) -> tuple[User, TokenPair]:
        if self.users.find_by_email(credentials.email) is not None:
            raise ApiError("EMAIL_ALREADY_EXISTS", "Пользователь с таким email уже существует", 409)

        user = User(email=credentials.email, password_hash=hash_password(credentials.password))
        self.users.add(user)
        try:
            db.session.flush()
            tokens = self._issue_tokens(user)
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ApiError(
                "EMAIL_ALREADY_EXISTS", "Пользователь с таким email уже существует", 409
            ) from error
        return user, tokens

    def login(self, credentials: Credentials) -> tuple[User, TokenPair]:
        user = self.users.find_by_email(credentials.email)
        if user is None or not verify_password(user.password_hash, credentials.password):
            raise ApiError("INVALID_CREDENTIALS", "Неверный email или пароль", 401)
        tokens = self._issue_tokens(user)
        db.session.commit()
        return user, tokens

    def refresh(self, user: User, current_jti: str) -> TokenPair:
        if not self.refresh_tokens.revoke(current_jti):
            raise ApiError("TOKEN_REVOKED", "Refresh token отозван", 401)
        tokens = self._issue_tokens(user)
        db.session.commit()
        return tokens

    def logout(self, jti: str) -> None:
        if not self.refresh_tokens.revoke(jti):
            raise ApiError("TOKEN_REVOKED", "Refresh token отозван", 401)
        db.session.commit()

    def get_user(self, public_id: str) -> User:
        user = self.users.find_by_public_id(public_id)
        if user is None:
            raise ApiError("USER_NOT_FOUND", "Пользователь не найден", 404)
        return user

    def _issue_tokens(self, user: User) -> TokenPair:
        identity = str(user.public_id)
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        decoded = decode_token(refresh_token)
        self.refresh_tokens.add(
            RefreshToken(
                jti=decoded["jti"],
                user_id=user.id,
                expires_at=datetime.fromtimestamp(decoded["exp"], tz=UTC),
            )
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

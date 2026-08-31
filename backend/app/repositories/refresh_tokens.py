from datetime import UTC, datetime

from sqlalchemy import select

from app.extensions import db
from app.models import RefreshToken


class RefreshTokenRepository:
    def find_by_jti(self, jti: str) -> RefreshToken | None:
        return db.session.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    def is_revoked_or_unknown(self, jti: str) -> bool:
        token = self.find_by_jti(jti)
        return token is None or token.revoked_at is not None

    def add(self, token: RefreshToken) -> None:
        db.session.add(token)

    def revoke(self, jti: str) -> bool:
        token = db.session.scalar(
            select(RefreshToken).where(RefreshToken.jti == jti).with_for_update()
        )
        if token is None or token.revoked_at is not None:
            return False
        token.revoked_at = datetime.now(UTC)
        return True

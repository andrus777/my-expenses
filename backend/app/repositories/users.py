import uuid

from sqlalchemy import select

from app.extensions import db
from app.models import User


class UserRepository:
    def find_by_email(self, email: str) -> User | None:
        return db.session.scalar(select(User).where(User.email == email))

    def find_by_public_id(self, public_id: str) -> User | None:
        try:
            parsed_public_id = uuid.UUID(public_id)
        except ValueError:
            return None
        return db.session.scalar(select(User).where(User.public_id == parsed_public_id))

    def add(self, user: User) -> None:
        db.session.add(user)

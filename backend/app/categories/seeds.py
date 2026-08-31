import uuid

from app.extensions import db
from app.models import Category

SYSTEM_CATEGORIES = (
    ("10000000-0000-0000-0000-000000000001", "Продукты"),
    ("10000000-0000-0000-0000-000000000002", "Транспорт"),
    ("10000000-0000-0000-0000-000000000003", "Жильё"),
    ("10000000-0000-0000-0000-000000000004", "Здоровье"),
    ("10000000-0000-0000-0000-000000000005", "Развлечения"),
    ("10000000-0000-0000-0000-000000000006", "Покупки"),
    ("10000000-0000-0000-0000-000000000007", "Образование"),
    ("10000000-0000-0000-0000-000000000008", "Другое"),
)


def seed_system_categories() -> None:
    for public_id, name in SYSTEM_CATEGORIES:
        db.session.add(
            Category(public_id=uuid.UUID(public_id), name=name, normalized_name=name.casefold())
        )
    db.session.commit()

import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

import click
from flask import Flask

from app.auth.passwords import hash_password
from app.extensions import db
from app.models import Budget, Category, Expense, Subscription, User

DEMO_EMAIL = "demo@my-expenses.local"


def seed_demo_data(email: str, password: str) -> tuple[User, bool]:
    """Create deterministic, interview-friendly demo data once."""
    existing = db.session.scalar(db.select(User).where(User.email == email.lower()))
    if existing is not None:
        return existing, False

    categories = list(
        db.session.scalars(
            db.select(Category).where(Category.user_id.is_(None)).order_by(Category.id)
        )
    )
    if not categories:
        raise click.ClickException("System categories are missing; run 'flask db upgrade' first")

    user = User(email=email.lower(), password_hash=hash_password(password))
    db.session.add(user)
    db.session.flush()

    today = date.today()
    rng = random.Random(20260902)
    merchants = ("Пятёрочка", "Метро", "Аптека", "Кофейня", "Маркетплейс")
    for index in range(40):
        category = categories[index % len(categories)]
        amount = Decimal(rng.randrange(15000, 850000)) / Decimal(100)
        db.session.add(
            Expense(
                user_id=user.id,
                category_id=category.id,
                category=category,
                amount=amount.quantize(Decimal("0.01")),
                currency="RUB",
                expense_date=today - timedelta(days=index % 35),
                merchant=merchants[index % len(merchants)],
                description=f"Демонстрационный расход {index + 1}",
                source="MANUAL",
                client_operation_id=uuid.uuid5(uuid.NAMESPACE_URL, f"my-expenses-demo-{index}"),
            )
        )

    subscriptions = (
        ("Музыка", Decimal("299.00"), "MONTHLY", today + timedelta(days=3)),
        ("Облачное хранилище", Decimal("1490.00"), "YEARLY", today + timedelta(days=14)),
        ("Спортзал", Decimal("2500.00"), "MONTHLY", today + timedelta(days=7)),
    )
    for index, (name, amount, frequency, next_date) in enumerate(subscriptions):
        db.session.add(
            Subscription(
                user_id=user.id,
                category_id=categories[(index + 4) % len(categories)].id,
                name=name,
                amount=amount,
                currency="RUB",
                frequency=frequency,
                custom_interval_days=None,
                billing_day=next_date.day,
                next_payment_date=next_date,
                comment="Демонстрационная подписка",
                is_active=True,
            )
        )

    month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    for category, amount in zip(categories[:3], ("25000.00", "8000.00", "15000.00"), strict=True):
        db.session.add(
            Budget(
                user_id=user.id,
                category_id=category.id,
                amount=Decimal(amount),
                currency="RUB",
                period="MONTH",
                start_date=month_start,
                end_date=month_end,
            )
        )

    db.session.commit()
    return user, True


def register_seed_command(app: Flask) -> None:
    @app.cli.command("seed-demo")
    @click.option("--email", default=DEMO_EMAIL, show_default=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def seed_demo(email: str, password: str) -> None:
        """Create a demo user and representative portfolio data."""
        if len(password) < 8:
            raise click.ClickException("Password must contain at least 8 characters")
        user, created = seed_demo_data(email, password)
        state = "created" if created else "already exists; no changes made"
        click.echo(f"Demo user {user.email}: {state}")

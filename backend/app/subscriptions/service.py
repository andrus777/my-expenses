from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.extensions import db
from app.models import Expense, Subscription, SubscriptionPayment, User
from app.repositories.categories import CategoryRepository
from app.repositories.subscriptions import SubscriptionRepository
from app.subscriptions.calculator import calculate_next_payment_date


class SubscriptionService:
    def __init__(self, calculator=calculate_next_payment_date) -> None:  # type: ignore[no-untyped-def]
        self.subscriptions = SubscriptionRepository()
        self.categories = CategoryRepository()
        self.calculator = calculator

    def list(self, user: User) -> list[Subscription]:
        return self.subscriptions.list(user.id)

    def get(self, public_id: uuid.UUID, user: User) -> Subscription:
        subscription = self.subscriptions.find(public_id, user.id)
        if subscription is None:
            raise ApiError("SUBSCRIPTION_NOT_FOUND", "Подписка не найдена", 404)
        return subscription

    def create(self, values: dict, user: User) -> Subscription:
        category = self._category(values.pop("category_public_id"), user)
        self._normalize_frequency(values)
        next_date = values["next_payment_date"]
        subscription = Subscription(
            user_id=user.id,
            category_id=category.id,
            category=category,
            billing_day=next_date.day,
            currency=values.pop("currency", "RUB"),
            is_active=values.pop("is_active", True),
            **values,
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription

    def update(self, public_id: uuid.UUID, values: dict, user: User) -> Subscription:
        subscription = self.get(public_id, user)
        category_id = values.pop("category_public_id", None)
        if category_id is not None:
            category = self._category(category_id, user)
            subscription.category_id = category.id
            subscription.category = category
        if "next_payment_date" in values:
            subscription.billing_day = values["next_payment_date"].day
        merged = {
            "frequency": values.get("frequency", subscription.frequency),
            "custom_interval_days": values.get(
                "custom_interval_days", subscription.custom_interval_days
            ),
        }
        self._normalize_frequency(merged)
        values["custom_interval_days"] = merged["custom_interval_days"]
        for field, value in values.items():
            setattr(subscription, field, value)
        db.session.commit()
        return subscription

    def delete(self, public_id: uuid.UUID, user: User) -> None:
        subscription = self.get(public_id, user)
        subscription.deleted_at = datetime.now(UTC)
        subscription.is_active = False
        db.session.commit()

    def payments(self, public_id: uuid.UUID, user: User) -> list[SubscriptionPayment]:
        return self.subscriptions.payments(self.get(public_id, user).id)

    def pay(
        self,
        public_id: uuid.UUID,
        operation_id: uuid.UUID,
        payment_date: date | None,
        user: User,
    ) -> tuple[SubscriptionPayment, bool]:
        subscription = self.get(public_id, user)
        existing = self.subscriptions.find_payment(subscription.id, operation_id)
        if existing is not None:
            if payment_date is not None and existing.payment_date != payment_date:
                raise ApiError(
                    "PAYMENT_OPERATION_CONFLICT", "Идентификатор оплаты уже использован", 409
                )
            return existing, False
        paid_on = payment_date or date.today()
        expense = Expense(
            user_id=user.id,
            category_id=subscription.category_id,
            category=subscription.category,
            amount=subscription.amount,
            currency=subscription.currency,
            expense_date=paid_on,
            merchant=subscription.name,
            description="Оплата подписки",
            comment=subscription.comment,
            source="SUBSCRIPTION",
            client_operation_id=operation_id,
        )
        payment = SubscriptionPayment(
            subscription=subscription,
            expense=expense,
            client_operation_id=operation_id,
            payment_date=paid_on,
            amount=subscription.amount,
        )
        db.session.add_all([expense, payment])
        try:
            subscription.next_payment_date = self.calculator(
                subscription.next_payment_date,
                subscription.frequency,
                subscription.billing_day,
                subscription.custom_interval_days,
            )
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            existing = self.subscriptions.find_payment(subscription.id, operation_id)
            if existing is not None and (
                payment_date is None or existing.payment_date == payment_date
            ):
                return existing, False
            raise ApiError(
                "PAYMENT_OPERATION_CONFLICT", "Идентификатор оплаты уже использован", 409
            ) from error
        except Exception:
            db.session.rollback()
            raise
        return payment, True

    def _category(self, public_id: uuid.UUID, user: User):  # type: ignore[no-untyped-def]
        category = self.categories.find_visible(public_id, user.id)
        if category is None:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
        return category

    @staticmethod
    def _normalize_frequency(values: dict) -> None:
        frequency = values["frequency"]
        if frequency == "CUSTOM":
            if not values.get("custom_interval_days"):
                raise ApiError(
                    "VALIDATION_ERROR",
                    "Для CUSTOM нужен интервал",
                    400,
                    {"custom_interval_days": ["Обязательное поле"]},
                )
        else:
            values["custom_interval_days"] = None

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Subscription, SubscriptionPayment


class SubscriptionRepository:
    def list(self, user_id: int) -> list[Subscription]:
        return list(
            db.session.scalars(
                select(Subscription)
                .options(joinedload(Subscription.category))
                .where(Subscription.user_id == user_id, Subscription.deleted_at.is_(None))
                .order_by(Subscription.next_payment_date)
            )
        )

    def find(self, public_id: uuid.UUID, user_id: int) -> Subscription | None:
        return db.session.scalar(
            select(Subscription)
            .options(joinedload(Subscription.category))
            .where(
                Subscription.public_id == public_id,
                Subscription.user_id == user_id,
                Subscription.deleted_at.is_(None),
            )
        )

    def find_payment(
        self, subscription_id: int, operation_id: uuid.UUID
    ) -> SubscriptionPayment | None:
        return db.session.scalar(
            select(SubscriptionPayment)
            .options(
                joinedload(SubscriptionPayment.subscription),
                joinedload(SubscriptionPayment.expense),
            )
            .where(
                SubscriptionPayment.subscription_id == subscription_id,
                SubscriptionPayment.client_operation_id == operation_id,
            )
        )

    def payments(self, subscription_id: int) -> list[SubscriptionPayment]:
        return list(
            db.session.scalars(
                select(SubscriptionPayment)
                .options(
                    joinedload(SubscriptionPayment.subscription),
                    joinedload(SubscriptionPayment.expense),
                )
                .where(SubscriptionPayment.subscription_id == subscription_id)
                .order_by(SubscriptionPayment.payment_date.desc(), SubscriptionPayment.id.desc())
            )
        )

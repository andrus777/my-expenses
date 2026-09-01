import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Receipt, ReceiptJob


class ReceiptRepository:
    def find_job(self, public_id: uuid.UUID, user_id: int | None = None) -> ReceiptJob | None:
        statement = (
            select(ReceiptJob)
            .options(joinedload(ReceiptJob.receipt).joinedload(Receipt.items))
            .where(ReceiptJob.public_id == public_id)
        )
        if user_id is not None:
            statement = statement.where(ReceiptJob.user_id == user_id)
        return db.session.scalar(statement)

    def find_job_for_update(self, public_id: uuid.UUID) -> ReceiptJob | None:
        return db.session.scalar(
            select(ReceiptJob).where(ReceiptJob.public_id == public_id).with_for_update()
        )

    def find_receipt(self, public_id: uuid.UUID, user_id: int) -> Receipt | None:
        return db.session.scalar(
            select(Receipt)
            .options(joinedload(Receipt.items), joinedload(Receipt.finalized_expense))
            .where(Receipt.public_id == public_id, Receipt.user_id == user_id)
        )

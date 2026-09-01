import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.extensions import db
from app.models import Expense, Receipt, ReceiptItem, ReceiptJob, User
from app.receipts.provider import NormalizedReceipt, ReceiptProvider
from app.repositories.categories import CategoryRepository
from app.repositories.expenses import ExpenseRepository
from app.repositories.receipts import ReceiptRepository


class ReceiptService:
    def __init__(self) -> None:
        self.receipts = ReceiptRepository()
        self.categories = CategoryRepository()
        self.expenses = ExpenseRepository()

    def create_job(self, receipt_data: str, user: User) -> ReceiptJob:
        if not receipt_data.strip() or len(receipt_data) > 4096:
            raise ApiError("VALIDATION_ERROR", "Некорректные данные чека", 400)
        job = ReceiptJob(user_id=user.id, receipt_data=receipt_data.strip(), status="PENDING")
        db.session.add(job)
        db.session.commit()
        return job

    def get_job(self, public_id: uuid.UUID, user: User) -> ReceiptJob:
        job = self.receipts.find_job(public_id, user.id)
        if job is None:
            raise ApiError("RECEIPT_JOB_NOT_FOUND", "Задание не найдено", 404)
        return job

    def process(
        self, public_id: uuid.UUID, provider: ReceiptProvider, provider_name: str
    ) -> ReceiptJob:
        job = self.receipts.find_job_for_update(public_id)
        if job is None:
            raise LookupError("receipt job not found")
        if job.status in {"COMPLETED", "PROCESSING"}:
            return job
        job.status = "PROCESSING"
        job.attempts += 1
        job.error_code = None
        job.error_message = None
        db.session.commit()
        normalized = provider.fetch(job.receipt_data)
        return self.complete(job, normalized, provider_name)

    def complete(self, job: ReceiptJob, data: NormalizedReceipt, provider_name: str) -> ReceiptJob:
        receipt = Receipt(
            user_id=job.user_id,
            provider=provider_name,
            provider_receipt_id=data.provider_receipt_id,
            merchant=data.merchant,
            total=data.total,
            currency=data.currency,
            purchase_date=data.purchase_date,
            items=[
                ReceiptItem(
                    name=item.name, quantity=item.quantity, price=item.price, total=item.total
                )
                for item in data.items
            ],
        )
        job.receipt = receipt
        job.status = "COMPLETED"
        db.session.add(receipt)
        db.session.commit()
        return job

    def mark_pending_retry(self, public_id: uuid.UUID, message: str) -> None:
        job = self.receipts.find_job(public_id)
        if job:
            job.status = "PENDING"
            job.error_code = "PROVIDER_TEMPORARY_ERROR"
            job.error_message = message[:500]
            db.session.commit()

    def mark_failed(self, public_id: uuid.UUID, code: str, message: str) -> None:
        job = self.receipts.find_job(public_id)
        if job:
            job.status = "FAILED"
            job.error_code = code
            job.error_message = message[:500]
            db.session.commit()

    def finalize(
        self, receipt_id: uuid.UUID, category_id: uuid.UUID, operation_id: uuid.UUID, user: User
    ) -> tuple[Expense, bool]:
        receipt = self.receipts.find_receipt(receipt_id, user.id)
        if receipt is None:
            raise ApiError("RECEIPT_NOT_FOUND", "Чек не найден", 404)
        if receipt.finalized_expense is not None:
            if receipt.finalized_expense.client_operation_id != operation_id:
                raise ApiError("RECEIPT_ALREADY_FINALIZED", "Чек уже подтверждён", 409)
            return receipt.finalized_expense, False
        category = self.categories.find_visible(category_id, user.id)
        if category is None:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
        existing = self.expenses.find_by_client_operation(operation_id, user.id)
        if existing is not None:
            raise ApiError(
                "CLIENT_OPERATION_CONFLICT", "Идентификатор операции уже использован", 409
            )
        expense = Expense(
            user_id=user.id,
            category_id=category.id,
            category=category,
            amount=receipt.total,
            currency=receipt.currency,
            expense_date=receipt.purchase_date,
            merchant=receipt.merchant,
            description="Расход по кассовому чеку",
            source="RECEIPT",
            client_operation_id=operation_id,
        )
        receipt.finalized_expense = expense
        receipt.finalized_at = datetime.now(UTC)
        db.session.add(expense)
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            refreshed = self.receipts.find_receipt(receipt_id, user.id)
            if (
                refreshed
                and refreshed.finalized_expense
                and refreshed.finalized_expense.client_operation_id == operation_id
            ):
                return refreshed.finalized_expense, False
            raise ApiError(
                "RECEIPT_FINALIZATION_CONFLICT", "Чек не удалось подтвердить повторно", 409
            ) from error
        return expense, True

import uuid

from app.celery_app import celery
from app.receipts.provider import PermanentProviderError, TemporaryProviderError
from app.receipts.providers import get_receipt_provider
from app.receipts.service import ReceiptService


@celery.task(bind=True, max_retries=3)
def process_receipt_job(self, job_id: str) -> None:  # type: ignore[no-untyped-def]
    service = ReceiptService()
    try:
        provider = get_receipt_provider()
        provider_name = (
            "external" if provider.__class__.__name__ == "ExternalReceiptProvider" else "fake"
        )
        service.process(uuid.UUID(job_id), provider, provider_name)
    except TemporaryProviderError as error:
        if self.request.retries >= self.max_retries:
            service.mark_failed(
                uuid.UUID(job_id), "PROVIDER_TIMEOUT", "Провайдер временно недоступен"
            )
            return
        service.mark_pending_retry(uuid.UUID(job_id), "Провайдер временно недоступен")
        raise self.retry(exc=error, countdown=retry_countdown(self.request.retries)) from error
    except PermanentProviderError:
        service.mark_failed(
            uuid.UUID(job_id), "PROVIDER_INVALID_RESPONSE", "Не удалось распознать чек"
        )
    except Exception:
        service.mark_failed(uuid.UUID(job_id), "PROCESSING_FAILED", "Не удалось обработать чек")
        raise


def retry_countdown(retries: int) -> int:
    return 2 ** (retries + 1)

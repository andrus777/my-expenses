from flask import current_app

from app.integrations.external_receipt_provider import ExternalReceiptProvider
from app.receipts.fake_provider import FakeReceiptProvider
from app.receipts.provider import ReceiptProvider


def get_receipt_provider() -> ReceiptProvider:
    provider = current_app.config["RECEIPT_PROVIDER"]
    if provider == "fake":
        return FakeReceiptProvider()
    if provider == "external":
        api_key = current_app.config.get("RECEIPT_PROVIDER_API_KEY")
        url = current_app.config.get("RECEIPT_PROVIDER_URL")
        if not api_key or not url:
            raise RuntimeError("External receipt provider is not configured")
        return ExternalReceiptProvider(
            url=url,
            api_key=api_key,
            timeout_seconds=current_app.config["RECEIPT_PROVIDER_TIMEOUT_SECONDS"],
        )
    raise RuntimeError(f"Unknown receipt provider: {provider}")

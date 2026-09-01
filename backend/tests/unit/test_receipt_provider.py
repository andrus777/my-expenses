import urllib.error
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.integrations.external_receipt_provider import ExternalReceiptProvider
from app.receipts.fake_provider import FakeReceiptProvider
from app.receipts.provider import PermanentProviderError, ReceiptProvider, TemporaryProviderError


def test_fake_provider_normalizes_receipt():
    provider: ReceiptProvider = FakeReceiptProvider()

    receipt = provider.fetch("qr-test-value")

    assert receipt.merchant == "Тестовый магазин"
    assert receipt.total == Decimal("350.00")
    assert sum(item.total for item in receipt.items) == receipt.total


@pytest.mark.parametrize("status", [408, 425, 429, 500, 503])
def test_external_provider_retries_only_temporary_http_statuses(status):
    error = urllib.error.HTTPError("https://provider.invalid", status, "failed", {}, None)
    provider = ExternalReceiptProvider("https://provider.invalid", "secret", 2.5)
    with patch("urllib.request.urlopen", side_effect=error), pytest.raises(TemporaryProviderError):
        provider.fetch("receipt")


def test_external_provider_does_not_retry_permanent_http_error():
    error = urllib.error.HTTPError("https://provider.invalid", 400, "failed", {}, None)
    provider = ExternalReceiptProvider("https://provider.invalid", "secret", 2.5)
    with patch("urllib.request.urlopen", side_effect=error), pytest.raises(PermanentProviderError):
        provider.fetch("receipt")

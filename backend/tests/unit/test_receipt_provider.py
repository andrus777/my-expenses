from decimal import Decimal

from app.receipts.fake_provider import FakeReceiptProvider
from app.receipts.provider import ReceiptProvider


def test_fake_provider_normalizes_receipt():
    provider: ReceiptProvider = FakeReceiptProvider()

    receipt = provider.fetch("qr-test-value")

    assert receipt.merchant == "Тестовый магазин"
    assert receipt.total == Decimal("350.00")
    assert sum(item.total for item in receipt.items) == receipt.total

from datetime import date
from decimal import Decimal

from app.receipts.provider import NormalizedReceipt, NormalizedReceiptItem


class FakeReceiptProvider:
    def fetch(self, receipt_data: str) -> NormalizedReceipt:
        suffix = receipt_data[-8:] if receipt_data else "local"
        return NormalizedReceipt(
            merchant="Тестовый магазин",
            total=Decimal("350.00"),
            currency="RUB",
            purchase_date=date(2026, 9, 1),
            provider_receipt_id=f"fake-{suffix}",
            items=(
                NormalizedReceiptItem(
                    "Молоко", Decimal("2.000"), Decimal("100.00"), Decimal("200.00")
                ),
                NormalizedReceiptItem(
                    "Хлеб", Decimal("1.000"), Decimal("150.00"), Decimal("150.00")
                ),
            ),
        )

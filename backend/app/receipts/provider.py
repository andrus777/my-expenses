from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


class TemporaryProviderError(Exception):
    """A provider failure that may succeed when retried."""


class PermanentProviderError(Exception):
    """A provider failure that must not be retried."""


@dataclass(frozen=True)
class NormalizedReceiptItem:
    name: str
    quantity: Decimal
    price: Decimal
    total: Decimal


@dataclass(frozen=True)
class NormalizedReceipt:
    merchant: str
    total: Decimal
    currency: str
    purchase_date: date
    items: tuple[NormalizedReceiptItem, ...]
    provider_receipt_id: str | None = None


class ReceiptProvider(Protocol):
    def fetch(self, receipt_data: str) -> NormalizedReceipt: ...

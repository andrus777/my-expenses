import json
import urllib.error
import urllib.request
from datetime import date
from decimal import Decimal

from app.receipts.provider import (
    NormalizedReceipt,
    NormalizedReceiptItem,
    PermanentProviderError,
    TemporaryProviderError,
)


class ExternalReceiptProvider:
    """HTTP adapter. Provider-specific JSON is normalized at this boundary."""

    def __init__(self, url: str, api_key: str, timeout_seconds: float) -> None:
        self.url = url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def fetch(self, receipt_data: str) -> NormalizedReceipt:
        request = urllib.request.Request(
            self.url,
            data=json.dumps({"receipt_data": receipt_data}).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in {408, 425, 429} or 500 <= error.code < 600:
                raise TemporaryProviderError("receipt provider temporarily unavailable") from error
            raise PermanentProviderError("receipt provider rejected the request") from error
        except (TimeoutError, urllib.error.URLError) as error:
            raise TemporaryProviderError("receipt provider temporarily unavailable") from error
        except (ValueError, KeyError, TypeError) as error:
            raise PermanentProviderError("receipt provider returned invalid data") from error
        try:
            items = tuple(
                NormalizedReceiptItem(
                    name=str(item["name"]),
                    quantity=Decimal(str(item["quantity"])),
                    price=Decimal(str(item["price"])),
                    total=Decimal(str(item["total"])),
                )
                for item in payload["items"]
            )
            return NormalizedReceipt(
                merchant=str(payload["merchant"]),
                total=Decimal(str(payload["total"])),
                currency=str(payload.get("currency", "RUB")).upper(),
                purchase_date=date.fromisoformat(payload["purchase_date"]),
                items=items,
                provider_receipt_id=payload.get("id"),
            )
        except (ValueError, KeyError, TypeError) as error:
            raise PermanentProviderError("receipt provider returned invalid data") from error

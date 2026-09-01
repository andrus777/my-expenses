# ADR 0005: Receipt provider boundary and asynchronous jobs

## Status

Accepted.

## Decision

Android submits fiscal/QR data only to the My Expenses backend. A `ReceiptProvider` protocol
isolates provider-specific formats and returns a normalized receipt DTO. Development and tests use
`FakeReceiptProvider`; the HTTP adapter is selected explicitly with `RECEIPT_PROVIDER=external`
and reads its URL, API key and timeout only from environment configuration.

The request creates a durable `ReceiptJob` in `PENDING`. Celery moves it through `PROCESSING` to
`COMPLETED` or `FAILED`, retrying temporary provider errors three times with exponential backoff.
Normalized previews are persisted as `Receipt` and `ReceiptItem` records.

Finalization is a separate authenticated operation. It atomically creates one Expense and links it
to the receipt. A client-generated operation UUID makes retries idempotent; a different UUID after
finalization returns a conflict.

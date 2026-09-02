# ADR 004: ReceiptProvider boundary and Redis/Celery jobs

## Status

Accepted.

## Decision

Provider-specific HTTP code implements `ReceiptProvider` and normalizes responses into internal
DTOs. Android calls only the backend. The API persists a PENDING job and Celery processes it through
Redis, with bounded HTTP timeouts and retry/backoff for temporary errors. Development and tests use
`FakeReceiptProvider` without credentials.

## Consequences

Slow external I/O does not occupy request workers, provider changes are isolated, and tests are
deterministic. PostgreSQL remains the durable source for job status and normalized previews.

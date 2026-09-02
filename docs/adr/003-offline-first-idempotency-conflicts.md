# ADR 003: Offline-first expenses, idempotency and conflict policy

## Status

Accepted.

## Decision

Room is the Android expense source of truth. Mutations are persisted locally before WorkManager
synchronizes them. Every create has a device UUID `client_operation_id`; PostgreSQL uniquely
constrains `(user_id, client_operation_id)`. Equivalent retries return the existing resource and
incompatible reuse returns HTTP 409.

For MVP edits use last-write-wins. The server `updated_at` is authoritative during reconciliation.
Soft-deleted expenses are excluded from normal reads and calculations.

## Consequences

The UI remains usable offline and retried creates cannot duplicate expenses. Concurrent edits are
simple and predictable, but a future multi-device version may require explicit optimistic locking.

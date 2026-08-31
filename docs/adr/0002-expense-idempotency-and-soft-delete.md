# ADR 0002: Expense mutation idempotency and soft deletion

## Status

Accepted — 2026-08-31

## Context

The Android client will create expenses offline and retry synchronization after network failures. A retried create must not produce a second financial operation. Deleted records must remain available for future synchronization and audit behavior.

## Decision

Every expense create request includes a client-generated UUID `client_operation_id`. PostgreSQL enforces uniqueness on `(user_id, client_operation_id)`.

If a request repeats an existing operation with equivalent business fields, the API returns the existing expense with HTTP 200. If the same operation ID is reused with different data, the API returns `CLIENT_OPERATION_CONFLICT` with HTTP 409. The comparison and insert run in one transaction, and the unique constraint handles concurrent races.

Expense deletion sets `deleted_at` in UTC. Normal reads, lists, updates and subsequent deletes exclude soft-deleted rows. The original `client_operation_id` remains reserved after deletion.

## Consequences

- Network retries cannot create duplicate expenses for one user.
- Different users may independently use the same client operation UUID.
- Storage is not reclaimed by normal deletion; retention and purge rules are deferred.
- A later full synchronization protocol can use the preserved deletion state without changing this API invariant.

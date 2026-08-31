# ADR 0003: Android offline-first expense synchronization

## Status

Accepted.

## Decision

Room is the Android source of truth for expenses. UI observes Room through `Flow` and never
waits for an HTTP response to show a mutation. Every local expense has a device-generated
`client_operation_id`, `syncStatus`, and a pending action (`CREATE`, `UPDATE`, or `DELETE`).

WorkManager runs a unique, network-constrained synchronization chain with exponential backoff.
Temporary network, rate-limit, and 5xx failures are retried. Permanent validation/conflict
failures become `SYNC_ERROR` and require an explicit user retry after correction.

Creation is idempotent through the backend unique `(user_id, client_operation_id)` constraint.
After a successful request, the server id and timestamps replace the corresponding local values.
The worker then pulls all server pages and reconciles them with Room. For edits, the MVP uses
last-write-wins: the server response is authoritative. Local deletes disappear immediately and
remain as hidden tombstones until the backend soft-delete succeeds.

Categories are cached in Room as supporting reference data, scoped by the authenticated public
user id. Expense data is scoped the same way so changing accounts cannot expose another local
profile's records.

## Consequences

- Adding, editing, and deleting remains usable without connectivity once categories are cached.
- A first installation needs one successful connection to load categories.
- Concurrent edits from multiple devices use last-write-wins; optimistic version conflicts are
  deliberately deferred.

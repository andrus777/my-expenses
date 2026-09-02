# Offline expense synchronization sequence

```mermaid
sequenceDiagram
  actor User
  participant UI as Compose UI
  participant Room
  participant WM as WorkManager
  participant API as Flask API
  participant DB as PostgreSQL

  User->>UI: Save expense
  UI->>Room: Insert local row (PENDING_SYNC, client_operation_id)
  Room-->>UI: Flow emits immediately
  UI->>WM: Enqueue unique network-constrained work
  WM->>API: POST /api/v1/expenses
  API->>DB: INSERT, unique(user_id, client_operation_id)
  alt first attempt
    DB-->>API: Created
    API-->>WM: 201 + server expense
  else equivalent retry
    DB-->>API: Existing operation
    API-->>WM: 200 + same expense
  else incompatible reuse
    API-->>WM: 409 CLIENT_OPERATION_CONFLICT
  end
  WM->>Room: Reconcile IDs/timestamps; mark SYNCED
  Room-->>UI: Flow emits authoritative state
```

Temporary network and 5xx failures use exponential backoff. Permanent validation/conflict failures
become `SYNC_ERROR`; the UI exposes a retry after correction. The current edit conflict policy is
last-write-wins using server `updated_at` as the authoritative timestamp.

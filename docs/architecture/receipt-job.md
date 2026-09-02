# Receipt job sequence

```mermaid
sequenceDiagram
  actor User
  participant Android
  participant API
  participant Redis
  participant Worker as Celery worker
  participant Provider as ReceiptProvider
  participant DB as PostgreSQL

  User->>Android: Submit receipt/QR data
  Android->>API: POST /api/v1/receipts
  API->>DB: Create ReceiptJob(PENDING)
  API->>Redis: Enqueue job ID
  API-->>Android: 202 job_id, PENDING
  Redis-->>Worker: Deliver job
  Worker->>DB: Set PROCESSING
  Worker->>Provider: fetch(receipt_data), bounded timeout
  alt success
    Provider-->>Worker: Provider response
    Worker->>Worker: Normalize to internal DTO
    Worker->>DB: Store Receipt/items; COMPLETED
  else temporary failure
    Worker->>DB: Restore PENDING + safe error
    Worker->>Redis: Retry with backoff
  else permanent/final failure
    Worker->>DB: Set FAILED + safe error
  end
  loop Until terminal state
    Android->>API: GET /api/v1/receipts/jobs/{job_id}
    API-->>Android: Status / normalized preview
  end
  User->>Android: Confirm preview
  Android->>API: POST /api/v1/receipts/{id}/finalize
  API->>DB: Atomically create Expense and mark finalized
  API-->>Android: 201, or 200 on equivalent retry
```

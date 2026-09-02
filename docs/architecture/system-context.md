# System and container architecture

The Android application is the only end-user client. It communicates with the My Expenses API;
external receipt providers are reachable only from the backend.

```mermaid
C4Context
  title My Expenses — system context
  Person(user, "User", "Tracks expenses and subscriptions")
  System(myExpenses, "My Expenses", "Offline-first personal expense tracking")
  System_Ext(receiptProvider, "Receipt provider", "Resolves fiscal/QR receipt data")
  Rel(user, myExpenses, "Uses", "Android")
  Rel(myExpenses, receiptProvider, "Requests normalized receipt data", "HTTPS")
```

```mermaid
C4Container
  title My Expenses — containers
  Person(user, "User")
  Container(android, "Android app", "Kotlin, Compose, Room, WorkManager", "Local-first UI and sync")
  Container(api, "API", "Flask, Gunicorn", "Auth and domain services")
  Container(worker, "Worker", "Celery", "Asynchronous receipt processing")
  ContainerDb(postgres, "Database", "PostgreSQL", "Authoritative business data")
  ContainerDb(redis, "Redis", "Redis", "Celery broker and rate-limit storage")
  System_Ext(provider, "Receipt provider")
  Rel(user, android, "Uses")
  Rel(android, api, "JSON/HTTPS + JWT")
  Rel(api, postgres, "SQL")
  Rel(api, redis, "Queues jobs / rate limits")
  Rel(worker, redis, "Consumes jobs")
  Rel(worker, postgres, "Updates job and receipt")
  Rel(worker, provider, "HTTPS with timeout/retry")
```

In production, TLS termination and secret injection are deployment concerns outside this local
Compose topology. The API remains stateless except for PostgreSQL and Redis-backed state.

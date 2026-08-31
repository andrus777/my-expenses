# AGENTS.md — My Expenses

## 1. Project goal

My Expenses is a portfolio-grade client-server Android application for personal expense tracking.
It is intentionally more serious than a CRUD demo and must demonstrate production-oriented engineering practices.

Core stack:
- Android: Kotlin, Jetpack Compose, Material 3, Navigation Compose, Retrofit, OkHttp, Room, DataStore, Coroutines, Flow/StateFlow, WorkManager.
- Backend: Python 3.12+, Flask, SQLAlchemy 2.x, Flask-Migrate/Alembic, PostgreSQL, JWT, Redis, Celery (or RQ if the repository already uses it), pytest.
- Infrastructure: Docker, Docker Compose, GitHub Actions.

Primary functional domains:
- authentication;
- expenses and categories;
- offline-first synchronization;
- subscriptions and subscription payments;
- receipt processing via external API provider;
- statistics and period comparison;
- category budgets and budget thresholds.

The project must remain understandable enough to discuss at a technical interview.
Do not introduce complexity only to imitate enterprise architecture.

---

## 2. Repository structure

Expected top-level structure:

my-expenses/
  android/
  backend/
  docs/
    adr/
    architecture/
  postman/ or bruno/
  .github/workflows/
  docker-compose.yml
  .env.example
  README.md
  AGENTS.md

Backend should be modular. Do not implement the backend as one large app.py file.

Preferred backend structure:

backend/app/
  api/v1/
  auth/
  users/
  categories/
  expenses/
  subscriptions/
  receipts/
  analytics/
  budgets/
  integrations/
  tasks/
  repositories/
  services/
  schemas/
  models/
  config.py
  extensions.py
  __init__.py

Android should separate UI, presentation, domain/use-cases where useful, repositories, local storage and remote API sources.

---

## 3. General implementation rules

Before changing code:
1. Inspect the existing repository and relevant modules.
2. Identify current public interfaces, models, migrations and tests.
3. Prefer the smallest coherent change that completes the task.
4. Do not rewrite working modules merely to match a personal preference.
5. Preserve backward compatibility unless the current task explicitly changes a contract.

After changing code:
1. Add or update tests.
2. Run the relevant unit tests.
3. Run integration tests for affected API flows.
4. Run linters/formatters.
5. Build the Android application when Android code is affected.
6. Briefly summarize what changed, migrations added, tests run and any remaining limitations.

Do not claim that a check passed unless it was actually executed.

---

## 4. Backend architecture rules

HTTP routes/controllers are thin adapters.
They may:
- parse request data;
- validate authentication/authorization context;
- call application services;
- map service results to HTTP responses.

Routes must not contain substantial business logic.
Routes must not contain long sequences of SQLAlchemy queries.

Business rules belong in services/domain code.
Database access belongs in repositories or small dedicated persistence abstractions where appropriate.

Preferred flow:
HTTP controller -> application service -> repository/domain -> PostgreSQL

Do not create abstractions with no real responsibility. Repository/service separation should improve testability and readability, not multiply boilerplate.

---

## 5. API conventions

All user-facing API endpoints must be versioned under:
/api/v1/

Use JSON request/response bodies.

Use consistent error responses:

{
  "error": {
    "code": "EXPENSE_NOT_FOUND",
    "message": "Расход не найден",
    "details": {}
  },
  "request_id": "..."
}

Use appropriate HTTP status codes.

For resources owned by users, choose one consistent policy for access to another user's resource.
Preferred policy: return 404 to avoid leaking resource existence.

Lists that may grow must support pagination.
Expense list must support filtering and sorting.

Use PATCH for partial updates unless there is a concrete reason to replace the whole resource.

---

## 6. Authentication and security

Passwords must never be stored or logged in plain text.
Use Argon2 or bcrypt for password hashing.

Use short-lived JWT access tokens and refresh tokens.
Refresh tokens must be revocable.

Secrets must come from environment variables.
Never commit:
- .env;
- JWT secrets;
- database passwords;
- external API keys;
- production credentials.

Never log:
- passwords;
- full JWT tokens;
- refresh tokens;
- external API keys.

Add rate limiting to authentication endpoints.

All object-level authorization checks must be enforced on the backend even if Android hides inaccessible UI actions.

---

## 7. Money and time rules

Never use float/double for persisted monetary values.
Backend money fields must use Decimal and PostgreSQL NUMERIC/DECIMAL.
Android must avoid floating-point arithmetic for financial calculations; use integer minor units or BigDecimal where appropriate.

Every persisted financial operation must have an explicit currency code.
MVP default currency is RUB, but the data model must not assume that RUB is the only possible currency forever.

Store timestamps in UTC on the backend.
Convert to local time only at presentation boundaries.
Expense date may remain a calendar date when time-of-day is not semantically required.

---

## 8. Database rules

Use migrations for every schema change.
Do not use db.create_all() as a production migration strategy.

Use database constraints for important invariants in addition to application validation.
Examples:
- amount > 0;
- unique email;
- unique (user_id, client_operation_id) for offline synchronization.

Add indexes intentionally for common access patterns, especially:
- (user_id, expense_date);
- category filtering;
- subscriptions by next_payment_date;
- receipt jobs by user/status where needed.

Critical multi-step financial operations must run inside a database transaction.

Do not physically delete expenses by default. Use soft delete where defined by the model and exclude deleted rows from normal queries.

---

## 9. Idempotency rules

Operations that can be retried due to network failure must not create duplicates.

Idempotency is required for at least:
- offline expense synchronization;
- subscription payment confirmation;
- receipt import/finalization where retries are possible.

Android-generated expense mutations must include client_operation_id (UUID).
Backend must enforce uniqueness for the user.

If an Idempotency-Key mechanism is implemented for HTTP operations, retries with the same key and equivalent request must return the already-created result rather than perform the operation again.

---

## 10. Offline-first Android rules

The Android expense workflow is offline-first.

When the user creates an expense:
1. Persist it to Room immediately.
2. Mark synchronization state PENDING_SYNC.
3. Update UI from local data without waiting for the network.
4. Schedule synchronization via WorkManager.
5. On success, reconcile local and server identifiers/version data and mark SYNCED.
6. On recoverable failure, retry with backoff.
7. On permanent validation/conflict failure, mark SYNC_ERROR and expose a user-friendly recovery path.

Synchronization must tolerate retries without duplicate server records.

The UI must not expose raw networking exceptions.

Use immutable UI state and StateFlow/Flow for screen state.

---

## 11. Conflict strategy

For MVP, Last Write Wins may be used for simple editable entities if the server owns the authoritative updated_at/version value.

Do not silently overwrite data if the backend can reliably detect an incompatible update.
If optimistic locking/versioning is introduced, return a clear conflict response and make it testable.

Document the chosen conflict behavior in an ADR.

---

## 12. Subscription rules

A subscription is not merely an expense with a repeat flag.
Keep Subscription and SubscriptionPayment as separate concepts.

Confirming a subscription payment must atomically:
1. create the Expense;
2. create/update SubscriptionPayment history;
3. calculate next_payment_date.

If any step fails, roll back the whole transaction.

Subscription frequency calculation must be implemented in a testable service and covered for edge cases such as month length and leap years.

Do not create duplicate expenses when a payment request is retried.

---

## 13. Receipt integration rules

The application must not depend directly on one external receipt API schema.

Use a provider abstraction, for example:
ReceiptProvider -> ExternalReceiptProvider

Normalize external responses into an internal receipt DTO/model before business logic consumes them.

External API keys stay on the backend only.
Android never calls the external receipt provider directly.

Potentially slow receipt processing must run as a background job through Redis + worker.

Receipt job states:
PENDING -> PROCESSING -> COMPLETED or FAILED

Store enough failure information for diagnosis, but never expose secret/provider internals to the end user.

Provide a mock/fake provider for tests and local development.

---

## 14. Analytics rules

Large aggregations belong on the backend, not in Android.

Required analytical capabilities:
- total expenses for a period;
- operation count;
- average daily expense;
- category distribution;
- timeline aggregation;
- current vs previous period comparison;
- subscription totals;
- budget usage.

Use database aggregation where practical.
Avoid loading all user expenses into Python just to sum them.

Analytics calculations must have deterministic tests for date boundaries and empty periods.

---

## 15. Budget rules

Budgets belong to a user and normally to a category/period.

Backend must calculate:
- budget_amount;
- spent_amount;
- remaining_amount;
- usage_percent.

Threshold events should support at least 80% and 100% usage without repeatedly generating the same alert for the same period.

Budget calculations must exclude soft-deleted expenses.

---

## 16. Background tasks

Do not perform slow external I/O or expensive processing inside the request thread when it can exceed normal API latency.

Use Redis + Celery/RQ for:
- receipt provider calls;
- selected asynchronous recalculations;
- background maintenance tasks.

Tasks must be idempotent where retries are enabled.

Configure retry/backoff intentionally.
Do not retry permanent validation errors indefinitely.

---

## 17. Logging and observability

Use Python logging, not print().

Every backend request should have a request/correlation ID.
If X-Request-ID is absent, generate one.
Return request_id in error responses.

Prefer structured logs in production.
Useful fields include:
- request_id;
- user_id when known;
- method;
- path;
- response status;
- duration_ms;
- job_id for background work.

Add:
GET /health
GET /ready

/ready should verify required infrastructure such as PostgreSQL and Redis.

---

## 18. Testing policy

Backend tests are mandatory.
Use pytest.

Separate where practical:
- unit tests for pure business logic;
- integration/API tests for Flask + database behavior.

Required security regression test:
User A must never read/update/delete User B's expense, subscription, receipt or budget.

Required idempotency tests:
Repeated equivalent requests must not duplicate business operations.

Required transaction tests:
A failure during subscription payment or receipt finalization must not leave partial persisted state.

Android must include at least:
- ViewModel tests;
- Repository tests;
- synchronization tests.

Tests must not depend on a real external receipt service. Use mocks/fakes.

---

## 19. Code quality

Backend target tools:
- ruff;
- black (unless Ruff formatter is explicitly selected for the project);
- mypy where practical;
- pytest.

Android target tools:
- ktlint;
- detekt;
- Gradle unit tests.

Prefer type hints in Python services, repositories and DTOs.

Avoid:
- giant functions;
- duplicate business rules;
- catch-all `except Exception: pass`;
- hidden global mutable state;
- SQL in UI code;
- HTTP calls directly from Composables;
- hard-coded environment URLs/secrets.

---

## 20. Documentation policy

Keep README current enough to run the project from a clean checkout.

Maintain OpenAPI/Swagger documentation for public REST endpoints.

Add ADRs for meaningful architectural decisions.
Minimum ADR set expected by the end of the project:
- PostgreSQL choice;
- JWT/refresh strategy;
- offline-first synchronization and idempotency;
- receipt provider abstraction and background jobs;
- conflict resolution strategy.

When API behavior or environment configuration changes, update documentation in the same task/commit.

---

## 21. Git and commit policy

Each requested development stage should result in one coherent commit unless a migration/fix must be separated for safety.

Use conventional-style commit messages where possible:
- feat:
- fix:
- test:
- docs:
- ci:
- refactor:
- chore:

Do not mix unrelated refactoring into a feature commit.

Do not rewrite repository history unless explicitly instructed.

---

## 22. Definition of done for any task

A task is not complete until:
- requested behavior exists;
- database migration is included when needed;
- validation and authorization are implemented;
- tests for the new behavior exist;
- relevant existing tests pass;
- lint/format checks pass;
- Android builds when Android is changed;
- API/docs are updated when contracts change;
- no secrets are introduced;
- implementation follows this AGENTS.md.

At the end of every task, report:
1. changed files/modules;
2. migrations;
3. tests added;
4. commands/checks executed and results;
5. known limitations or deliberate deferrals;
6. suggested commit message.

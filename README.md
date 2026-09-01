# My Expenses

Portfolio-grade client-server application for personal expense tracking.

## Stage 1: local infrastructure

Prerequisites: Docker with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

The API is available at `http://localhost:8000`:

- `GET /health` reports that the process is alive;
- `GET /ready` checks PostgreSQL and Redis connectivity.

Run backend checks locally with Python 3.12+:

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"  # Windows
.venv/Scripts/pytest
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .
```

Database migrations are managed with Flask-Migrate. Stage 2 introduces users and authentication; apply its migration before using the API:

```bash
docker compose exec api flask --app wsgi:app db upgrade
```

Authentication endpoints are under `/api/v1`:

- `POST /auth/register` and `POST /auth/login` accept `email` and `password`;
- `POST /auth/refresh` and `POST /auth/logout` require a refresh bearer token;
- `GET /users/me` requires an access bearer token.

Access tokens expire after 15 minutes. Refresh tokens expire after 30 days, rotate on refresh, and are stored server-side so logout and rotation revoke them immediately. See `docs/openapi.yaml` for the HTTP contract.

Stage 3 adds system and user categories plus offline-safe expense CRUD:

- `GET|POST /api/v1/categories` and `GET|PATCH|DELETE /api/v1/categories/{id}`;
- `GET|POST /api/v1/expenses` and `GET|PATCH|DELETE /api/v1/expenses/{id}`;
- expense amounts are decimal strings such as `"1250.50"`;
- every expense mutation carries a UUID `client_operation_id`;
- expense deletion is soft deletion;
- expense lists support pagination, dates, category, amount, currency, source, search and sorting filters.

System categories are inserted by migration and cannot be changed or deleted. User-owned resources are always scoped to the authenticated user.

## Repository layout

- `android/` — Kotlin/Compose Android client
- `backend/` — Flask API and Celery worker
- `docs/` — architecture and ADR documentation
- `postman/` — API collections (introduced with public APIs)

## Android client

Stage 4 provides registration, login, session restoration through `GET /api/v1/users/me`,
and the main four-tab application shell. Tokens are encrypted with an Android Keystore key
before being persisted in DataStore; Room stores only the non-secret cached user profile.

Stage 5 makes expenses offline-first. Adds, edits and deletes update Room immediately and are
sent by a network-constrained WorkManager job. Pending operations survive process restarts,
temporary failures use exponential backoff, and permanent failures are shown as `SYNC_ERROR`
with a manual retry action. Categories must be loaded online once before the first offline add.
See `docs/adr/0003-android-offline-first-expense-sync.md` for reconciliation details.

Stage 6 adds subscription CRUD and atomic, idempotent payment confirmation. Each confirmed payment
creates an expense, appends payment history and advances the next payment date. The Android client
shows upcoming payments and schedules local notifications 7, 3 and 1 day before payment at 09:00.
Notification permission is requested on Android 13 and newer.

Stage 7 adds asynchronous receipt processing. `POST /api/v1/receipts` accepts fiscal/QR text and
queues a Celery job; Android polls the backend for a normalized preview and never contacts an
external receipt service. Local development uses `RECEIPT_PROVIDER=fake` and requires no API key.
Set `RECEIPT_PROVIDER=external`, URL, key and timeout environment variables only when configuring a
real adapter. Receipt confirmation is a separate idempotent operation that creates one Expense.

Stage 8 adds authenticated backend analytics under `/api/v1/statistics`: summary and previous-period
comparison, category distribution, day/week/month timeline, and projected subscription totals.
Date ranges are inclusive and accept `date_from`/`date_to` in ISO format. The Android Statistics tab
supports week, month, year and custom periods with explicit loading, empty and error states.
Analytics never mixes currencies: `currency` defaults to `RUB`, and no exchange-rate conversion is implied.

The debug build connects to `http://10.0.2.2:8000/api/v1/` from the Android emulator.
Override it when needed with `-PAPI_BASE_URL=https://example.com/api/v1/`. Cleartext traffic
is enabled only for debug builds. Build and run unit tests with:

```bash
cd android
./gradlew testDebugUnitTest assembleDebug ktlintCheck
```

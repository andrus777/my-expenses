# My Expenses

Portfolio-grade client-server expense tracker: an offline-first Android application backed by a
production-oriented Flask API. It covers authentication, expenses, subscriptions, asynchronous
receipt recognition, analytics and category budgets.

## Architecture

- **Android:** Kotlin, Jetpack Compose/Material 3, Navigation, Room, DataStore, Retrofit/OkHttp,
  Coroutines/Flow and WorkManager.
- **API:** Python 3.12+, Flask application factory, SQLAlchemy 2.x, Alembic, JWT and Gunicorn.
- **Data and jobs:** PostgreSQL is authoritative; Redis backs rate limiting and Celery jobs.
- **Boundaries:** routes adapt HTTP, services own rules, repositories own queries, and receipt
  provider payloads are normalized behind a backend-only interface.

See the [system/container diagram](docs/architecture/system-context.md),
[offline sync sequence](docs/architecture/offline-expense-sync.md),
[receipt job sequence](docs/architecture/receipt-job.md), and [ADRs](docs/adr).

## Local run

Prerequisites: Git and Docker with Compose v2. Android additionally needs Android Studio/JDK 17.
From a clean checkout:

```bash
git clone https://github.com/andrus777/my-expenses.git
cd my-expenses
cp .env.example .env
docker compose up -d --build
docker compose exec api flask --app wsgi:app db upgrade
```

PowerShell copy command: `Copy-Item .env.example .env`. The values are local placeholders; replace
database and JWT secrets before any shared deployment. Verify the stack:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
docker compose ps
```

`/health` is process liveness. `/ready` requires PostgreSQL and Redis. The API runs under Gunicorn
at `http://localhost:8000`; the worker consumes receipt jobs independently.

Create representative demo data (one user, 40 expenses, 3 subscriptions, 3 budgets):

```bash
docker compose exec api flask --app wsgi:app seed-demo --email demo@my-expenses.local
```

The password is prompted, so it is not stored in the repository or shell history. The command is
idempotent per email. System categories come from migrations. Stop with `docker compose down`; add
`--volumes` only when intentionally erasing local data.

### Android

Open `android/` in Android Studio with JDK 17 and run `app` on an emulator. Debug calls
`http://10.0.2.2:8000/api/v1/`. A physical device needs a reachable host address:

```bash
cd android
./gradlew assembleDebug -PAPI_BASE_URL=http://192.168.1.10:8000/api/v1/
```

Cleartext HTTP is debug-only; production endpoints must use HTTPS.

## API

The complete OpenAPI 3.1 contract is [docs/openapi.yaml](docs/openapi.yaml). Import it into Swagger
Editor/UI, or serve a local viewer:

```bash
docker run --rm -p 8081:8080 -e SWAGGER_JSON=/spec/openapi.yaml \
  -v "$PWD/docs:/spec:ro" swaggerapi/swagger-ui
```

Swagger UI is then at `http://localhost:8081`. Import the
[Postman collection](postman/My-Expenses.postman_collection.json), set its password to the value
entered for `seed-demo`, and run Login. Public groups cover auth/users, categories/expenses,
subscriptions/payments, receipts/jobs, statistics and budgets.

All errors use one contract:

```json
{
  "error": {"code": "EXPENSE_NOT_FOUND", "message": "Расход не найден", "details": {}},
  "request_id": "correlation-id"
}
```

Owned resources return 404 when absent or owned by another user, avoiding existence leaks.

## Offline Sync

Room is the expense source of truth. Mutations appear immediately as `PENDING_SYNC`; a
network-constrained WorkManager job sends them later. Device `client_operation_id` UUIDs and a
PostgreSQL unique constraint make creates idempotent. Successful responses reconcile server data
and become `SYNCED`; transient failures back off, while permanent failures become `SYNC_ERROR`.
MVP edits use last-write-wins with the server timestamp authoritative. See
[ADR 003](docs/adr/003-offline-first-idempotency-conflicts.md).

## Security

- Passwords use Argon2; passwords, tokens and API keys are never logged.
- Access JWTs last 15 minutes; 30-day refresh tokens rotate and have PostgreSQL revoke records.
- Auth endpoints are Redis-rate-limited; Android encrypts auth state using Android Keystore.
- Backend object authorization is mandatory and regression-tested. Receipt credentials stay on the
  backend.
- Every response carries `X-Request-ID`; JSON logs contain safe request metadata only.

Configuration and bounded infrastructure/HTTP timeouts are documented in [.env.example](.env.example).

## Testing

Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .
.venv/Scripts/mypy
.venv/Scripts/pytest --cov=app --cov-report=term-missing --cov-report=xml
```

Use `.venv/bin/...` on Unix. Ruff is the formatter/linter, mypy checks typed core paths, branch
coverage must remain at least 85%, and tests use only the fake receipt provider.

Android gate:

```bash
cd android
./gradlew ktlintCheck detekt lintDebug testDebugUnitTest assembleDebug --no-daemon
```

From the root, install hooks with `backend/.venv/Scripts/pre-commit install` (or the Unix `bin`
path), then run `backend/.venv/Scripts/pre-commit run --all-files`.

## CI/CD

[GitHub Actions](.github/workflows/ci.yml) runs on push and pull requests. Backend uses Python 3.12
and PostgreSQL 17, validates migrations, lint/format, mypy, pytest and coverage. Android runs ktlint,
detekt, lint, unit tests and `assembleDebug` on JDK 17. Dependency caches contain no app secrets.

This repository produces a tested build, not a production deployment. Production needs injected
unique secrets, TLS, backups and an environment-specific database.

## Screenshots

Use the reproducible, non-personal demo data and follow the
[capture checklist](docs/screenshots/README.md). Add images only after visual review.

## Roadmap

- Multi-device optimistic locking beyond MVP last-write-wins.
- Explicit exchange rates and consolidated multi-currency reporting.
- Production receipt provider integration and contract monitoring.
- Release signing, deployment and backup/restore runbooks.
- Accessibility/device-matrix UI tests and polished portfolio screenshots.

## Repository layout

```text
android/             Android application
backend/             Flask API, Celery worker, migrations and tests
docs/adr/            Architecture decisions
docs/architecture/   System and sequence diagrams
docs/openapi.yaml    OpenAPI 3.1 specification
postman/             Importable API collection
.github/workflows/   CI quality gates
```

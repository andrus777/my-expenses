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

## Repository layout

- `android/` — Android client (introduced in a later stage)
- `backend/` — Flask API and Celery worker
- `docs/` — architecture and ADR documentation
- `postman/` — API collections (introduced with public APIs)

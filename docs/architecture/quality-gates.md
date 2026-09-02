# Quality gates

The project uses one reproducible gate set locally and in GitHub Actions.

## Backend

- `ruff check .` performs Python linting.
- `ruff format --check .` is the only Python formatting policy; Black is intentionally not mixed in.
- `mypy` checks the typed core where annotations provide useful guarantees without suppressing
  Flask/SQLAlchemy dynamic behavior across the whole application.
- `pytest --cov=app --cov-report=term-missing --cov-report=xml` runs unit and integration tests,
  measures branch coverage, writes `coverage.xml`, and fails below 85%.
- CI applies the complete Alembic chain and runs integration tests against PostgreSQL 17.

## Android

`./gradlew ktlintCheck detekt lintDebug testDebugUnitTest assembleDebug` is the Android gate.
Detekt uses the checked-in configuration under `android/config/detekt`; deliberate broad exception
handling in offline synchronization is locally suppressed only where cancellation is rethrown and
transient/permanent failures must be classified.

## Pre-commit

The repository-local hooks run Ruff lint, Ruff format verification, focused mypy, and staged diff
whitespace validation. Hooks never receive or cache application secrets.

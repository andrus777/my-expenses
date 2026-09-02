# ADR 001: PostgreSQL as the authoritative store

## Status

Accepted.

## Decision

PostgreSQL is the authoritative backend database. SQLAlchemy 2.x provides persistence and Alembic
migrations own schema evolution. PostgreSQL constraints enforce financial invariants and retry
idempotency; indexes support user/date/category and scheduled-payment access patterns.

SQLite is used only for fast isolated tests. Production schema management never uses
`db.create_all()`.

## Consequences

Local and CI environments need PostgreSQL. Decimal money maps to `NUMERIC`, transactions protect
multi-row financial workflows, and database-specific integration behavior is exercised in CI.

# ADR 0001: JWT access and refresh token strategy

## Status

Accepted — 2026-08-31

## Context

The Android client needs short-lived credentials for API calls and a way to renew a session without storing a password. Stateless refresh JWTs cannot be invalidated immediately after logout or credential compromise.

## Decision

The API issues a 15-minute JWT access token and a 30-day JWT refresh token. Each refresh token has a unique `jti` persisted in PostgreSQL. A refresh token is accepted only while its record exists and `revoked_at` is null.

Refresh rotates the current token: the old record is revoked and a new token record is created in the same database transaction. Logout revokes the supplied refresh token. Access tokens remain stateless and expire naturally after their short lifetime.

Passwords are hashed with Argon2id. Registration and login are rate-limited through Flask-Limiter using Redis outside tests.

## Consequences

- Logout and refresh-token replay are rejected immediately.
- PostgreSQL is consulted for each refresh-authenticated request, but normal access-token requests remain stateless.
- Expired refresh-token rows require a future maintenance task; this is deliberately deferred until background maintenance is introduced.
- Changing the JWT secret invalidates every outstanding token.

# ADR 002: JWT access tokens with refresh rotation and revocation

## Status

Accepted.

## Decision

Use 15-minute JWT access tokens and 30-day refresh tokens. Refresh-token JTIs are stored in
PostgreSQL; refresh rotates and revokes the previous token, while logout revokes it immediately.
Android encrypts auth state with an Android Keystore key before DataStore persistence.

## Consequences

Access verification stays inexpensive, compromised refresh tokens can be blocked server-side, and
access-token revocation is bounded by the short expiry. Passwords use Argon2 and auth endpoints are
rate-limited through Redis.

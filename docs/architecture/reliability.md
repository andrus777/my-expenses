# Reliability and observability

## Correlation IDs and logs

The API accepts a bounded, log-safe `X-Request-ID` or generates a UUID. It returns the ID in the
response header and in every error envelope. Request completion logs are single-line JSON with a
fixed allowlist of fields. Request/response bodies, query strings, authorization headers, passwords,
JWTs, refresh tokens and provider API keys are never included.

`LOG_LEVEL` controls Flask request logging. Celery uses the same configured level.

## Health policy

`GET /health` is a liveness probe and does not access infrastructure. `GET /ready` verifies both
PostgreSQL (`SELECT 1`, with a statement timeout) and Redis (`PING`, with connect/read timeouts).
It returns `503` with dependency availability states and the correlation `request_id` when either
dependency is unavailable.

## Errors and ownership

Framework and domain errors use the same envelope: `error.code`, `error.message`, `error.details`
and top-level `request_id`. Resources owned by another user consistently return `404`, not `403`,
to avoid disclosing their existence.

## External HTTP timeout policy

Receipt-provider calls always have a configured timeout. Network timeouts, HTTP 408/425/429 and
5xx responses are temporary and use the existing bounded Celery exponential retry. Other HTTP 4xx
responses and invalid provider payloads are permanent and are not retried. No provider error body
or credential is returned to clients or written to request logs.

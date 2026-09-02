# ADR 005: Server-side analytics and category budgets

## Status

Accepted.

## Decision

Aggregate expenses in PostgreSQL by authenticated user, date range and currency. No implicit
currency conversion is performed. Category budgets use explicit inclusive date bounds and calculate
spent values from non-deleted expenses. Unique durable events record the 80% and 100% thresholds
once per budget period.

## Consequences

Android receives compact presentation-ready series, calculations share one security boundary, and
empty/date-boundary behavior is deterministic. Cross-currency reporting requires a future explicit
exchange-rate policy.

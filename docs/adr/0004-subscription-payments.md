# ADR 0004: Subscription payment transaction and idempotency

## Status

Accepted.

## Decision

`Subscription` and `SubscriptionPayment` are separate entities. Confirming payment creates an
Expense with source `SUBSCRIPTION`, creates the payment history row, and advances the subscription
inside one SQLAlchemy transaction. Any exception rolls back all three changes.

The client supplies a UUID `client_operation_id`. It is unique both for the subscription payment
and for the user's generated Expense. An equivalent retry returns the existing payment with HTTP
200; reuse with a different payment date returns a conflict.

Calendar frequencies retain the subscription's original billing day. Dates that do not exist in a
target month are clamped to that month's final day without losing the original anchor for future
calculations. Custom frequency is represented as a positive number of days.

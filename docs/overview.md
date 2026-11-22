# CareerOS Identity Service â€” service overview

## Responsibility

Authentication, authorization, account lifecycle and tenant isolation.

## Data ownership

User identity, sessions, roles and authorization decisions.

## Interfaces

- Inputs: Authentication and account-management requests.
- Outputs: Short-lived identity claims and account lifecycle events.
- Dependencies: External identity providers only through configured adapters.

## Contract rules

- APIs and events are versioned.
- Consumers must be idempotent where retries are possible.
- Correlation identifiers are propagated without logging sensitive payloads.
- Authorization and ownership are checked at the service boundary.

## Non-goals

This service does not absorb responsibilities owned by another CareerOS service. Cross-service workflows are coordinated through explicit contracts rather than shared databases.

## Security and privacy

Persist the minimum data required, record provenance, define retention, redact logs and use synthetic examples in this public repository.
# CareerOS Identity Service

Authentication, authorization, account lifecycle and tenant isolation.

## Scope

- **Owns:** User identity, sessions, roles and authorization decisions.
- **Inputs:** Authentication and account-management requests.
- **Outputs:** Short-lived identity claims and account lifecycle events.
- **Dependencies:** External identity providers only through configured adapters.

## Safety baseline

This public repository must never contain secrets, real resumes, real applications or personal data. External communication and application submission always require explicit user approval.

## Documentation

See [docs/overview.md](docs/overview.md) and the central [CareerOS workspace](https://github.com/FievezRomain/careeros-workspace).

## Status

Architecture and security baseline. Functional implementation will be added incrementally with tests and versioned contracts.

## License

Apache-2.0.
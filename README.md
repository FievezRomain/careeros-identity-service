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

## Local development

The service requires Python 3.14 and `uv` 0.13.9. Run `uv sync --locked --all-groups`, copy `.env.example` to `.env`, then start it with `uv run uvicorn careeros_identity.adapters.http:create_app --factory`. `APP_ENV` accepts `development`, `test` or `production`; `LOG_LEVEL` accepts `debug`, `info`, `warning` or `error`. Both are required, and missing, unknown or invalid values stop composition before the server starts.

`GET /health` reports process liveness and `GET /ready` reports readiness after startup configuration validation. These operational endpoints intentionally require no authentication and expose no configuration, user or provider data. Both return or create `X-Correlation-ID`. Keycloak connectivity is outside this scaffold and will extend readiness when its adapter is introduced.

The domain remains framework-independent. The application module owns use cases and future ports; the FastAPI adapter maps Pydantic boundary models and acts as the initial composition root.

## Authentication context

Authenticated use cases depend on `require_account_context`. It accepts only bearer JWTs signed with RS256, verifies issuer, audience, expiry, issued-at time and required identity claims against the configured Keycloak JWKS endpoint, then exposes an immutable Pydantic context containing `account_id`, `tenant_id`, deduplicated roles and deduplicated scopes. Failures return the same `401 UNAUTHENTICATED` response without revealing whether the signature, expiry or claim validation failed. JWKS network access is confined to the provider adapter and is replaced by an in-memory key resolver in tests.

## Status

Python service scaffold with validated configuration, operational endpoints and automated quality gates. Identity behavior will be added incrementally through versioned contracts.

## License

Apache-2.0.

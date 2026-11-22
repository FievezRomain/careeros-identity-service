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

## Status

Python service scaffold with validated configuration, operational endpoints and automated quality gates. Identity behavior will be added incrementally through versioned contracts.

## License

Apache-2.0.

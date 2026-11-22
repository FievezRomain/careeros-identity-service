"""FastAPI adapter and composition root for the identity service."""

import json
import logging
from typing import Annotated, Literal, cast
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import RequestResponseEndpoint

from careeros_identity.adapters.auth import JwtTokenVerifier, SigningKeyResolver
from careeros_identity.application import (
    AccountContext,
    TokenValidationError,
    TokenVerifier,
    health_status,
    readiness_status,
)

CORRELATION_HEADER = "X-Correlation-ID"
LOGGER = logging.getLogger("careeros.identity.http")
BEARER = HTTPBearer(auto_error=False)


class Settings(BaseSettings):
    """Validated, non-secret startup configuration."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        extra="forbid",
        frozen=True,
    )

    app_env: Literal["development", "test", "production"]
    log_level: Literal["debug", "info", "warning", "error"]
    oidc_issuer: AnyHttpUrl
    oidc_audience: str = Field(min_length=1)
    oidc_jwks_url: AnyHttpUrl


class HealthResponse(BaseModel):
    """HTTP boundary model without configuration or secret values."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    status: Literal["ok", "ready"]
    service: Literal["identity-service"] = "identity-service"


class AuthError(BaseModel):
    """Stable denial response without token validation details."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: Literal["UNAUTHENTICATED"] = "UNAUTHENTICATED"


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get(CORRELATION_HEADER, "")
    if (
        supplied
        and len(supplied) <= 128
        and all(character.isalnum() or character in "-_." for character in supplied)
    ):
        return supplied
    return str(uuid4())


def require_account_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(BEARER)],
) -> AccountContext:
    """Validate a bearer token and expose normalized identity to a use case."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthenticated()
    verifier = cast(TokenVerifier, request.app.state.token_verifier)
    try:
        return verifier.verify(credentials.credentials)
    except TokenValidationError:
        raise _unauthenticated() from None


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=AuthError().model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_app(
    settings: Settings | None = None, token_verifier: TokenVerifier | None = None
) -> FastAPI:
    """Validate configuration and compose the HTTP adapter."""
    validated_settings = settings or Settings()
    LOGGER.setLevel(validated_settings.log_level.upper())
    application = FastAPI(title="CareerOS Identity Service", version="0.1.0")
    application.state.settings = validated_settings
    application.state.token_verifier = token_verifier or JwtTokenVerifier(
        resolver=SigningKeyResolver(str(validated_settings.oidc_jwks_url)),
        issuer=str(validated_settings.oidc_issuer),
        audience=validated_settings.oidc_audience,
    )

    @application.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = _correlation_id(request)
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id
        LOGGER.info(
            json.dumps(
                {
                    "correlation_id": correlation_id,
                    "event": "http_request",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return response

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        return HealthResponse.model_validate(health_status())

    @application.get("/ready", response_model=HealthResponse, tags=["operations"])
    async def ready() -> HealthResponse:
        return HealthResponse.model_validate(readiness_status())

    return application

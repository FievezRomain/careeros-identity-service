"""FastAPI adapter and composition root for the identity service."""

import json
import logging
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import RequestResponseEndpoint

from careeros_identity.application import health_status, readiness_status

CORRELATION_HEADER = "X-Correlation-ID"
LOGGER = logging.getLogger("careeros.identity.http")


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


class HealthResponse(BaseModel):
    """HTTP boundary model without configuration or secret values."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    status: Literal["ok", "ready"]
    service: Literal["identity-service"] = "identity-service"


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get(CORRELATION_HEADER, "")
    if (
        supplied
        and len(supplied) <= 128
        and all(character.isalnum() or character in "-_." for character in supplied)
    ):
        return supplied
    return str(uuid4())


def create_app(settings: Settings | None = None) -> FastAPI:
    """Validate configuration and compose the HTTP adapter."""
    validated_settings = settings or Settings()
    LOGGER.setLevel(validated_settings.log_level.upper())
    application = FastAPI(title="CareerOS Identity Service", version="0.1.0")
    application.state.settings = validated_settings

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

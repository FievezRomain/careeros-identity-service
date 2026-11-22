"""Identity application layer and port ownership."""

from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OperationalStatus(BaseModel):
    """Pydantic model returned through the operational application port."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "ready"]
    service: Literal["identity-service"] = "identity-service"


class AccountContext(BaseModel):
    """Normalized, immutable identity facts exposed to use cases."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    account_id: UUID
    tenant_id: UUID
    roles: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()


class TokenValidationError(Exception):
    """A token cannot establish a trusted account context."""


class TokenVerifier(Protocol):
    """Inbound identity port implemented by a provider adapter."""

    def verify(self, token: str) -> AccountContext: ...


def health_status() -> OperationalStatus:
    """Return process liveness without consulting external providers."""
    return OperationalStatus(status="ok")


def readiness_status() -> OperationalStatus:
    """Return readiness after startup configuration has been validated."""
    return OperationalStatus(status="ready")

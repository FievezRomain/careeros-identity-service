"""Identity application layer and port ownership."""

from enum import StrEnum
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


class TenantTarget(BaseModel):
    """Tenant boundary a use case must authorize before accessing data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID


class OwnedTarget(BaseModel):
    """Ownership facts required to authorize access to a user-owned resource."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: UUID
    owner_account_id: UUID


class AuthorizationDenial(StrEnum):
    """Stable internal reasons for a denied authorization decision."""

    TENANT_MISMATCH = "TENANT_MISMATCH"
    OWNERSHIP_MISMATCH = "OWNERSHIP_MISMATCH"


class AuthorizationDenied(Exception):
    """The authenticated account cannot access the requested resource."""

    def __init__(self, reason: AuthorizationDenial) -> None:
        super().__init__("access denied")
        self.reason = reason


class AuthorizationPolicy:
    """Enforce tenant isolation and ownership inside application use cases."""

    def require_tenant_access(
        self,
        context: AccountContext,
        target: TenantTarget | OwnedTarget,
    ) -> None:
        if context.tenant_id != target.tenant_id:
            raise AuthorizationDenied(AuthorizationDenial.TENANT_MISMATCH)

    def require_ownership(self, context: AccountContext, target: OwnedTarget) -> None:
        self.require_tenant_access(context, target)
        if context.account_id != target.owner_account_id:
            raise AuthorizationDenied(AuthorizationDenial.OWNERSHIP_MISMATCH)


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

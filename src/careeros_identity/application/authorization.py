"""Tenant and resource-ownership authorization policy."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from careeros_identity.application.authentication import AccountContext


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

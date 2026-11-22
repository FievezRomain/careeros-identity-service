"""Authentication models and ports owned by the application layer."""

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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

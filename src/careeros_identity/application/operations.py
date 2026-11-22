"""Operational application queries."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class OperationalStatus(BaseModel):
    """Pydantic model returned through the operational application port."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "ready"]
    service: Literal["identity-service"] = "identity-service"


def health_status() -> OperationalStatus:
    """Return process liveness without consulting external providers."""
    return OperationalStatus(status="ok")


def readiness_status() -> OperationalStatus:
    """Return readiness after startup configuration has been validated."""
    return OperationalStatus(status="ready")

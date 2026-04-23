"""Response DTOs for deployment options sub-models."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class HandlerTimeoutEntryInfo(BaseResponseModel):
    """A single ``(handler_name, timeout_sec)`` entry."""

    handler_name: str = Field(description="Handler identifier.")
    timeout_sec: int | None = Field(
        description="Timeout in seconds; null means this handler is unbounded."
    )


class DeploymentTimeoutsInfo(BaseResponseModel):
    """Handler-keyed timeout policy."""

    default: int | None = Field(
        description="Fallback timeout in seconds; null means unbounded.",
    )
    by_handler: list[HandlerTimeoutEntryInfo] = Field(
        description="Per-handler timeout overrides.",
    )


class DeploymentOptionsInfo(BaseResponseModel):
    """Per-deployment (or per-resource-group default) options payload."""

    timeouts: DeploymentTimeoutsInfo = Field(description="Handler timeout policy.")

"""
Request DTOs for Service Catalog DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.types import ServiceCatalogStatus

__all__ = (
    "CreateServiceCatalogInput",
    "DeleteServiceCatalogInput",
    "EndpointInput",
    "HeartbeatInput",
    "UpdateServiceCatalogInput",
)


class EndpointInput(BaseRequestModel):
    """Input for a service catalog endpoint."""

    role: str = Field(min_length=1, max_length=32, description="Role of the endpoint")
    scope: str = Field(min_length=1, max_length=32, description="Scope of the endpoint")
    address: str = Field(
        min_length=1, max_length=256, description="Network address of the endpoint"
    )
    port: int = Field(ge=1, le=65535, description="Port number of the endpoint")
    protocol: str = Field(min_length=1, max_length=16, description="Protocol used by the endpoint")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata for the endpoint"
    )


class CreateServiceCatalogInput(BaseRequestModel):
    """Input for registering a new service catalog entry."""

    service_group: str = Field(
        min_length=1,
        max_length=64,
        description="Service group identifier",
    )
    instance_id: str = Field(
        min_length=1,
        max_length=128,
        description="Unique instance identifier within the service group",
    )
    display_name: str = Field(
        min_length=1,
        max_length=256,
        description="Human-readable display name for the service",
    )
    version: str = Field(
        min_length=1,
        max_length=64,
        description="Version string of the service",
    )
    labels: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value labels for the service",
    )
    status: ServiceCatalogStatus = Field(description="Current status of the service")
    startup_time: datetime = Field(description="Time when the service started")
    config_hash: str = Field(default="", description="Hash of the service configuration")
    endpoints: list[EndpointInput] | None = Field(
        default=None, description="List of endpoints exposed by the service"
    )

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("display_name must not be blank or whitespace-only")
        return stripped


class UpdateServiceCatalogInput(BaseRequestModel):
    """Input for updating an existing service catalog entry."""

    display_name: str | None = Field(
        default=None,
        description="Updated display name",
    )
    version: str | None = Field(default=None, description="Updated version string")
    labels: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL, description="Updated labels. Use SENTINEL to clear."
    )
    status: ServiceCatalogStatus | None = Field(default=None, description="Updated service status")
    config_hash: str | None = Field(default=None, description="Updated configuration hash")

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("display_name must not be blank or whitespace-only")
        return stripped


class DeleteServiceCatalogInput(BaseRequestModel):
    """Input for deleting a service catalog entry."""

    id: UUID = Field(description="Service catalog entry ID to delete")


class HeartbeatInput(BaseRequestModel):
    """Input for updating the heartbeat of a service catalog entry."""

    id: UUID = Field(description="Service catalog entry ID to heartbeat")

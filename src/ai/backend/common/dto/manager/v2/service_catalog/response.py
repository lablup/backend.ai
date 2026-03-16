"""
Response DTOs for Service Catalog DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
    ServiceCatalogStatus,
)

__all__ = (
    "CreateServiceCatalogPayload",
    "DeleteServiceCatalogPayload",
    "HeartbeatPayload",
    "ServiceCatalogNode",
    "UpdateServiceCatalogPayload",
)


class ServiceCatalogNode(BaseResponseModel):
    """Node model representing a service catalog entry."""

    id: UUID = Field(description="Service catalog entry ID")
    service_group: str = Field(description="Service group name")
    instance_id: str = Field(description="Unique instance identifier")
    display_name: str = Field(description="Human-readable display name")
    version: str = Field(description="Service version string")
    labels: dict[str, Any] = Field(default_factory=dict, description="Arbitrary key-value labels")
    status: ServiceCatalogStatus = Field(description="Current service catalog status")
    startup_time: datetime = Field(description="Service startup timestamp")
    registered_at: datetime = Field(description="Registration timestamp")
    last_heartbeat: datetime = Field(description="Last heartbeat timestamp")
    config_hash: str = Field(description="Hash of service configuration")
    endpoints: list[EndpointInfo] = Field(
        default_factory=list, description="List of service endpoints"
    )


class CreateServiceCatalogPayload(BaseResponseModel):
    """Payload for service catalog creation mutation result."""

    service: ServiceCatalogNode = Field(description="Created service catalog entry")


class UpdateServiceCatalogPayload(BaseResponseModel):
    """Payload for service catalog update mutation result."""

    service: ServiceCatalogNode = Field(description="Updated service catalog entry")


class DeleteServiceCatalogPayload(BaseResponseModel):
    """Payload for service catalog deletion mutation result."""

    id: UUID = Field(description="ID of the deleted service catalog entry")


class HeartbeatPayload(BaseResponseModel):
    """Payload for service catalog heartbeat mutation result."""

    success: bool = Field(description="Whether the heartbeat was recorded successfully")
    last_heartbeat: datetime = Field(description="Updated last heartbeat timestamp")

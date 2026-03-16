"""
Response DTOs for resource group DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "CreateResourceGroupPayload",
    "DeleteResourceGroupPayload",
    "ResourceGroupNode",
    "UpdateResourceGroupPayload",
)


class ResourceGroupNode(BaseResponseModel):
    """Node model representing a resource group entity."""

    id: UUID = Field(description="Resource group UUID.")
    name: str = Field(description="Unique name of the resource group.")
    domain_name: str = Field(description="Domain the resource group belongs to.")
    description: str | None = Field(
        default=None,
        description="Human-readable description of the resource group.",
    )
    is_active: bool = Field(
        description="Whether the resource group is active.",
    )
    total_resource_slots: dict[str, Any] = Field(
        description="Total resource slot limits for the resource group.",
    )
    allowed_vfolder_hosts: dict[str, Any] = Field(
        description="Allowed vfolder host permissions for the resource group.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External integration ID associated with this resource group.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Resource policy name applied to this resource group.",
    )
    created_at: datetime = Field(
        description="Timestamp when the resource group was created.",
    )
    modified_at: datetime = Field(
        description="Timestamp when the resource group was last modified.",
    )


class CreateResourceGroupPayload(BaseResponseModel):
    """Payload for resource group creation mutation result."""

    resource_group: ResourceGroupNode = Field(description="Created resource group.")


class UpdateResourceGroupPayload(BaseResponseModel):
    """Payload for resource group update mutation result."""

    resource_group: ResourceGroupNode = Field(description="Updated resource group.")


class DeleteResourceGroupPayload(BaseResponseModel):
    """Payload for resource group deletion mutation result."""

    id: UUID = Field(description="UUID of the deleted resource group.")

"""
Response DTOs for resource group DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchResourceGroupsPayload",
    "CreateResourceGroupPayload",
    "DeleteResourceGroupPayload",
    "ResourceGroupNode",
    "UpdateResourceGroupPayload",
    # GQL-layer sub-models
    "PreemptionConfigInfo",
    "ResourceGroupStatusInfo",
    "ResourceGroupMetadataInfo",
    "ResourceGroupNetworkConfigInfo",
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


class AdminSearchResourceGroupsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated resource group search results."""

    items: list[ResourceGroupNode] = Field(description="List of resource group nodes.")
    total_count: int = Field(description="Total number of resource groups matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


# GQL-layer sub-model DTOs


class _PreemptionOrderEnum(StrEnum):
    OLDEST = "oldest"
    NEWEST = "newest"


class _PreemptionModeEnum(StrEnum):
    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"


class PreemptionConfigInfo(BaseResponseModel):
    """GQL-layer preemption configuration DTO."""

    preemptible_priority: int = Field(
        description="Sessions with priority <= this value are eligible for preemption."
    )
    order: _PreemptionOrderEnum = Field(
        description="Tie-breaking order for same-priority sessions during preemption."
    )
    mode: _PreemptionModeEnum = Field(
        description="How to preempt a session when preemption is triggered."
    )


class ResourceGroupStatusInfo(BaseResponseModel):
    """GQL-layer status information DTO for a resource group."""

    is_active: bool = Field(
        description="Whether the resource group is active and can accept new sessions."
    )
    is_public: bool = Field(
        description="Whether the resource group is publicly accessible to all users."
    )


class ResourceGroupMetadataInfo(BaseResponseModel):
    """GQL-layer metadata DTO for a resource group."""

    description: str | None = Field(
        default=None,
        description="Human-readable description of the resource group.",
    )
    created_at: datetime = Field(description="Timestamp when the resource group was created.")


class ResourceGroupNetworkConfigInfo(BaseResponseModel):
    """GQL-layer network configuration DTO for a resource group."""

    wsproxy_addr: str | None = Field(
        default=None,
        description="WebSocket proxy address for this resource group.",
    )
    use_host_network: bool = Field(
        description="Whether to use host network mode for containers in this resource group."
    )

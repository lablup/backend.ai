"""
Response DTOs for resource group DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.fair_share.types import (
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    PreemptionOrderDTO,
    SchedulerTypeDTO,
)

__all__ = (
    "AdminSearchResourceGroupsPayload",
    "AllowedDomainsPayload",
    "AllowedProjectsPayload",
    "AllowedResourceGroupsPayload",
    "CreateResourceGroupPayload",
    "DeleteResourceGroupPayload",
    "FairShareScalingGroupSpecInfo",
    "PreemptionConfigInfo",
    "ResourceGroupDetailNode",
    "ResourceGroupMetadataInfo",
    "ResourceGroupNetworkConfigInfo",
    "ResourceGroupNode",
    "ResourceGroupSchedulerConfigInfo",
    "ResourceGroupStatusInfo",
    "ResourceInfoNode",
    "UpdateResourceGroupConfigPayloadNode",
    "UpdateResourceGroupFairShareSpecPayloadNode",
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
    integration_name: str | None = Field(
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

    items: list[ResourceGroupDetailNode] = Field(description="List of resource group nodes.")
    total_count: int = Field(description="Total number of resource groups matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


# GQL-layer sub-model DTOs


class PreemptionConfigInfo(BaseResponseModel):
    """Preemption configuration DTO."""

    preemptible_priority: int = Field(
        description="Sessions with priority <= this value are eligible for preemption."
    )
    order: PreemptionOrderDTO = Field(
        description="Tie-breaking order for same-priority sessions during preemption."
    )
    mode: PreemptionModeDTO = Field(
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


class ResourceGroupSchedulerConfigInfo(BaseResponseModel):
    """Scheduler configuration DTO for a resource group."""

    type: SchedulerTypeDTO = Field(
        description="Type of scheduler used for session scheduling (fifo, lifo, drf, fair-share)."
    )
    preemption: PreemptionConfigInfo = Field(
        description="Preemption configuration for this resource group."
    )


class ResourceGroupDetailNode(BaseResponseModel):
    """Detail node DTO for a resource group (GQL-layer representation)."""

    id: str = Field(description="Resource group name used as the relay node ID.")
    name: str = Field(description="Unique name of the resource group.")
    status: ResourceGroupStatusInfo = Field(
        description="Status information including active and public flags."
    )
    metadata: ResourceGroupMetadataInfo = Field(
        description="Metadata including description and creation timestamp."
    )
    network: ResourceGroupNetworkConfigInfo = Field(
        description="Network configuration for the resource group."
    )
    scheduler: ResourceGroupSchedulerConfigInfo = Field(
        description="Scheduler configuration for the resource group."
    )


class UpdateResourceGroupFairShareSpecPayloadNode(BaseResponseModel):
    """Payload DTO for resource group fair share spec update mutation."""

    resource_group: ResourceGroupDetailNode = Field(
        description="The updated resource group with new fair share configuration."
    )


class UpdateResourceGroupConfigPayloadNode(BaseResponseModel):
    """Payload DTO for resource group configuration update mutation."""

    resource_group: ResourceGroupDetailNode = Field(
        description="The updated resource group with new configuration."
    )


class FairShareScalingGroupSpecInfo(BaseResponseModel):
    """Fair share configuration for a resource group."""

    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    default_weight: Decimal = Field(
        description="Default weight for entities without explicit weight"
    )
    resource_weights: list[ResourceWeightEntryInfo] = Field(
        description="Weights for each resource type"
    )


class ResourceInfoNode(BaseResponseModel):
    """Resource information for a resource group."""

    capacity: ResourceSlotInfo = Field(description="Total available resources")
    used: ResourceSlotInfo = Field(description="Currently occupied resources")
    free: ResourceSlotInfo = Field(description="Available resources (capacity - used)")


class AllowedResourceGroupsPayload(BaseResponseModel):
    """Payload containing a list of allowed resource group names."""

    items: list[str] = Field(description="Allowed resource group names.")


class AllowedDomainsPayload(BaseResponseModel):
    """Payload containing a list of allowed domain names."""

    items: list[str] = Field(description="Allowed domain names.")


class AllowedProjectsPayload(BaseResponseModel):
    """Payload containing a list of allowed project IDs."""

    items: list[UUID] = Field(description="Allowed project IDs.")

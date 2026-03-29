"""Response DTOs for resource allocation v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
    ResourceLimitEntryInfo,
    ResourceSlotEntryInfo,
)

__all__ = (
    "CheckPresetAvailabilityPayload",
    "DomainResourceAllocationPayload",
    "EffectiveBreakdownNode",
    "EffectiveResourceAllocationPayload",
    "KeypairResourceAllocationPayload",
    "PresetAvailabilityNode",
    "ProjectResourceAllocationPayload",
    "ResourceGroupResourceAllocationPayload",
    "ResourceGroupUsageNode",
    "ScopeResourceUsageNode",
)


class ScopeResourceUsageNode(BaseResponseModel):
    """Resource usage for a single scope (keypair, project, domain)."""

    limits: list[ResourceLimitEntryInfo] = Field(description="Policy-defined resource limits.")
    used: list[ResourceSlotEntryInfo] = Field(description="Currently occupied resources.")
    assignable: list[ResourceLimitEntryInfo] = Field(
        description="Assignable resources within policy limits (limits - used)."
    )


class ResourceGroupUsageNode(BaseResponseModel):
    """Resource usage for a resource group (agent-level physical resources)."""

    capacity: list[ResourceSlotEntryInfo] = Field(description="Total agent capacity.")
    used: list[ResourceSlotEntryInfo] = Field(description="Currently occupied by sessions.")
    free: list[ResourceSlotEntryInfo] = Field(description="Free resources (capacity - used).")
    max_per_node: list[ResourceSlotEntryInfo] = Field(
        description="Largest single-agent free resources."
    )


class EffectiveBreakdownNode(BaseResponseModel):
    """Breakdown of resource allocation by scope."""

    keypair: ScopeResourceUsageNode = Field(description="Keypair resource policy limits.")
    project: ScopeResourceUsageNode | None = Field(
        default=None,
        description="Project resource limits. Null when group_resource_visibility is disabled.",
    )
    domain: ScopeResourceUsageNode = Field(description="Domain resource limits.")
    resource_group: ResourceGroupUsageNode | None = Field(
        default=None,
        description="Resource group physical resources. Null when hide_agents is enabled.",
    )


class EffectiveResourceAllocationPayload(BaseResponseModel):
    """Effective assignable resources considering all scope constraints."""

    assignable: list[ResourceLimitEntryInfo] = Field(
        description="Effective assignable resources (minimum across all scopes)."
    )
    breakdown: EffectiveBreakdownNode = Field(
        description="Per-scope breakdown of resource limits and usage."
    )


class PresetAvailabilityNode(BaseResponseModel):
    """A resource preset with its availability status."""

    id: UUID = Field(description="Resource preset UUID.")
    name: str = Field(description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryInfo] = Field(description="Resource slot allocations.")
    shared_memory: BinarySizeInfo | None = Field(default=None, description="Shared memory size.")
    resource_group_name: str | None = Field(
        default=None, description="Resource group name. Null means global preset."
    )
    available: bool = Field(description="Whether this preset can be used for session creation.")


class CheckPresetAvailabilityPayload(BaseResponseModel):
    """Payload containing preset availability check results."""

    presets: list[PresetAvailabilityNode] = Field(
        description="Resource presets with availability status."
    )


# Individual scope payloads (wrapper for consistency)


class KeypairResourceAllocationPayload(BaseResponseModel):
    """Payload for keypair resource allocation query."""

    keypair: ScopeResourceUsageNode = Field(description="Keypair resource usage.")


class ProjectResourceAllocationPayload(BaseResponseModel):
    """Payload for project resource allocation query."""

    project: ScopeResourceUsageNode = Field(description="Project resource usage.")


class DomainResourceAllocationPayload(BaseResponseModel):
    """Payload for domain resource allocation query."""

    domain: ScopeResourceUsageNode = Field(description="Domain resource usage.")


class ResourceGroupResourceAllocationPayload(BaseResponseModel):
    """Payload for resource group resource allocation query."""

    resource_group: ResourceGroupUsageNode = Field(description="Resource group resource usage.")

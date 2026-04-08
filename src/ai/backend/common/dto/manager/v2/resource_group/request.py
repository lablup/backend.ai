"""
Request DTOs for resource group DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
)

__all__ = (
    "AdminSearchResourceGroupsInput",
    "CreateResourceGroupInput",
    "DeleteResourceGroupInput",
    "PreemptionConfigInputDTO",
    "ResourceGroupFilter",
    "ResourceGroupOrder",
    "ResourceWeightEntryInput",
    "UpdateAllowedDomainsForResourceGroupInput",
    "UpdateAllowedProjectsForResourceGroupInput",
    "UpdateAllowedResourceGroupsForDomainInput",
    "UpdateAllowedResourceGroupsForProjectInput",
    "UpdateResourceGroupConfigInput",
    "UpdateResourceGroupFairShareSpecInput",
    "UpdateResourceGroupInput",
)


class CreateResourceGroupInput(BaseRequestModel):
    """Input for creating a new resource group."""

    name: str = Field(
        min_length=1,
        max_length=256,
        description="Resource group name. Must be non-empty after stripping whitespace.",
    )
    domain_name: str = Field(
        description="Domain name the resource group belongs to.",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of the resource group.",
    )
    total_resource_slots: dict[str, Any] | None = Field(
        default=None,
        description="Total resource slot limits for the resource group.",
    )
    allowed_vfolder_hosts: dict[str, Any] | None = Field(
        default=None,
        description="Allowed vfolder host permissions for the resource group.",
    )
    integration_name: str | None = Field(
        default=None,
        description="External integration ID associated with this resource group.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Resource policy name to apply to this resource group.",
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank after stripping whitespace")
        return stripped


class UpdateResourceGroupInput(BaseRequestModel):
    """Input for updating a resource group. All fields optional for partial update."""

    name: str | None = Field(
        default=None,
        description="Updated resource group name. Leave null to keep existing value.",
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description=("Updated description. Use SENTINEL to clear, null to keep existing value."),
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the resource group is active. Leave null to keep existing value.",
    )
    total_resource_slots: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated total resource slot limits. Use SENTINEL to clear, null to keep existing value."
        ),
    )
    allowed_vfolder_hosts: dict[str, Any] | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated allowed vfolder host permissions. "
            "Use SENTINEL to clear, null to keep existing value."
        ),
    )
    integration_name: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated external integration ID. Use SENTINEL to clear, null to keep existing value."
        ),
    )
    resource_policy: str | Sentinel | None = Field(
        default=SENTINEL,
        description=(
            "Updated resource policy name. Use SENTINEL to clear, null to keep existing value."
        ),
    )


class DeleteResourceGroupInput(BaseRequestModel):
    """Input for deleting a resource group."""

    id: UUID = Field(
        description="UUID of the resource group to delete.",
    )


class ResourceGroupFilter(BaseRequestModel):
    """Filter criteria for searching resource groups."""

    name: StringFilter | None = Field(default=None, description="Filter by name.")
    description: StringFilter | None = Field(default=None, description="Filter by description.")
    is_active: bool | None = Field(default=None, description="Filter by active status.")
    is_public: bool | None = Field(default=None, description="Filter by public status.")
    AND: list[ResourceGroupFilter] | None = Field(default=None, description="AND conjunction.")
    OR: list[ResourceGroupFilter] | None = Field(default=None, description="OR conjunction.")
    NOT: list[ResourceGroupFilter] | None = Field(default=None, description="NOT negation.")


ResourceGroupFilter.model_rebuild()


class ResourceGroupOrder(BaseRequestModel):
    """Order specification for resource group search results."""

    field: ResourceGroupOrderField = Field(description="Field to order by.")
    direction: ResourceGroupOrderDirection = Field(
        default=ResourceGroupOrderDirection.ASC, description="Order direction."
    )


class AdminSearchResourceGroupsInput(BaseRequestModel):
    """Input for admin search of resource groups with cursor and offset pagination."""

    filter: ResourceGroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ResourceGroupOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class ResourceWeightEntryInput(BaseRequestModel):
    """Input for a single resource weight entry."""

    resource_type: str = Field(description="Resource type identifier.")
    weight: Decimal | None = Field(
        default=None,
        description="Weight multiplier. Set null to revert to default weight.",
    )


class PreemptionConfigInputDTO(BaseRequestModel):
    """Input for preemption configuration."""

    preemptible_priority: int = Field(
        default=5,
        description="Sessions with priority <= this value are eligible for preemption.",
    )
    order: str = Field(
        default="oldest",
        description="Tie-breaking order for same-priority sessions (oldest/newest).",
    )
    mode: str = Field(
        default="terminate",
        description="How to preempt sessions (terminate/reschedule).",
    )


class UpdateResourceGroupFairShareSpecInput(BaseRequestModel):
    """Input for updating resource group fair share configuration (GQL-aligned)."""

    resource_group_name: str = Field(description="Name of the resource group to update.")
    half_life_days: int | None = Field(
        default=None,
        description="Half-life for exponential decay in days. Leave null to keep existing value.",
    )
    lookback_days: int | None = Field(
        default=None,
        description="Total lookback period in days. Leave null to keep existing value.",
    )
    decay_unit_days: int | None = Field(
        default=None,
        description="Granularity of decay buckets in days. Leave null to keep existing value.",
    )
    default_weight: Decimal | None = Field(
        default=None,
        description="Default weight for entities. Leave null to keep existing value.",
    )
    resource_weights: list[ResourceWeightEntryInput] | None = Field(
        default=None,
        description="Resource weights for fair share calculation. Leave null to keep existing values.",
    )


class UpdateResourceGroupConfigInput(BaseRequestModel):
    """Input for updating resource group configuration via GQL (all fields optional)."""

    resource_group_name: str = Field(description="Name of the resource group to update.")
    is_active: bool | None = Field(
        default=None,
        description="Whether the resource group is active. Leave null to keep existing value.",
    )
    is_public: bool | None = Field(
        default=None,
        description="Whether the resource group is public. Leave null to keep existing value.",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description. Leave null to keep existing value.",
    )
    app_proxy_addr: str | None = Field(
        default=None,
        description="App proxy address. Leave null to keep existing value.",
    )
    appproxy_api_token: str | None = Field(
        default=None,
        description="App proxy API token. Leave null to keep existing value.",
    )
    use_host_network: bool | None = Field(
        default=None,
        description="Whether to use host network mode. Leave null to keep existing value.",
    )
    scheduler_type: str | None = Field(
        default=None,
        description="Scheduler type value (fifo/lifo/drf/fair-share). Leave null to keep existing.",
    )
    preemption: PreemptionConfigInputDTO | None = Field(
        default=None,
        description="Preemption configuration. Leave null to keep existing value.",
    )


class UpdateAllowedResourceGroupsForDomainInput(BaseRequestModel):
    """Input for updating allowed resource groups for a domain."""

    domain_name: str = Field(description="Domain name to update allowed resource groups for.")
    add: list[str] | None = Field(default=None, description="Resource group names to allow.")
    remove: list[str] | None = Field(default=None, description="Resource group names to disallow.")


class UpdateAllowedResourceGroupsForProjectInput(BaseRequestModel):
    """Input for updating allowed resource groups for a project."""

    project_id: UUID = Field(description="Project ID to update allowed resource groups for.")
    add: list[str] | None = Field(default=None, description="Resource group names to allow.")
    remove: list[str] | None = Field(default=None, description="Resource group names to disallow.")


class UpdateAllowedDomainsForResourceGroupInput(BaseRequestModel):
    """Input for updating allowed domains for a resource group."""

    resource_group_name: str = Field(
        description="Resource group name to update allowed domains for."
    )
    add: list[str] | None = Field(default=None, description="Domain names to allow.")
    remove: list[str] | None = Field(default=None, description="Domain names to disallow.")


class UpdateAllowedProjectsForResourceGroupInput(BaseRequestModel):
    """Input for updating allowed projects for a resource group."""

    resource_group_name: str = Field(
        description="Resource group name to update allowed projects for."
    )
    add: list[UUID] | None = Field(default=None, description="Project IDs to allow.")
    remove: list[UUID] | None = Field(default=None, description="Project IDs to disallow.")

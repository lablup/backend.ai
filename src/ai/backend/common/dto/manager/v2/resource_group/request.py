"""
Request DTOs for resource group DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.deployment_options import DeploymentOptionsInput
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
    ResourceGroupScope,
)
from ai.backend.common.dto.manager.v2.session_options import DefaultSessionOptionsInput
from ai.backend.common.tristate.unset import UNSET, Unset
from ai.backend.common.types import PreemptionVictimScope

__all__ = (
    "AdminSearchResourceGroupsInput",
    "CreateResourceGroupInput",
    "DeleteResourceGroupInput",
    "PreemptionConfigInputDTO",
    "ReplaceResourceGroupDefaultDeploymentOptionsGQLInput",
    "ReplaceResourceGroupDefaultDeploymentOptionsInput",
    "ReplaceResourceGroupDefaultSessionOptionsGQLInput",
    "ReplaceResourceGroupDefaultSessionOptionsInput",
    "ResourceGroupFilter",
    "ResourceGroupOrder",
    "ResourceWeightEntryInput",
    "ScopedSearchResourceGroupsInput",
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
    is_default: bool = Field(
        default=False,
        description=(
            "Make this the default resource group. At most one resource group may hold the"
            " flag, so this is rejected while another one holds it; clear that one first."
        ),
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

    name: str | None | Unset = Field(
        default=UNSET,
        description="Updated resource group name. Omit to leave unchanged.",
    )
    description: str | None | Unset = Field(
        default=UNSET,
        description="Updated description. Omit to leave unchanged; null clears.",
    )
    is_active: bool | None | Unset = Field(
        default=UNSET,
        description="Whether the resource group is active. Omit to leave unchanged.",
    )
    is_default: bool | None | Unset = Field(
        default=UNSET,
        description=(
            "Whether this is the default resource group. At most one resource group may hold"
            " the flag, so setting it to true is rejected while another one holds it; clear"
            " that one first. Omit to leave unchanged."
        ),
    )
    total_resource_slots: dict[str, Any] | None | Unset = Field(
        default=UNSET,
        description="Updated total resource slot limits. Omit to leave unchanged; null clears.",
    )
    allowed_vfolder_hosts: dict[str, Any] | None | Unset = Field(
        default=UNSET,
        description=(
            "Updated allowed vfolder host permissions. Omit to leave unchanged; null clears."
        ),
    )
    integration_name: str | None | Unset = Field(
        default=UNSET,
        description="Updated external integration ID. Omit to leave unchanged; null clears.",
    )
    resource_policy: str | None | Unset = Field(
        default=UNSET,
        description="Updated resource policy name. Omit to leave unchanged; null clears.",
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
    is_default: bool | None = Field(
        default=None, description="Filter by whether the resource group is the default one."
    )
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


class ScopedSearchResourceGroupsInput(BaseRequestModel):
    """Input for searching the resource groups the named scopes reach."""

    scope: ResourceGroupScope = Field(description="Scope (OR across all items).")
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

    enabled: bool = Field(
        default=False,
        description="Whether preemption is enabled for this resource group (opt-in).",
    )
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
    preemption_min_runtime: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Minimum session runtime in seconds before it becomes preemptible (0 = disabled)."
        ),
    )
    victim_scope: PreemptionVictimScope = Field(
        default=PreemptionVictimScope.USER,
        description=(
            "Scope preemption victims are drawn from (user/project/domain/resource-group). "
            "Default is user."
        ),
    )


class UpdateResourceGroupFairShareSpecInput(BaseRequestModel):
    """Input for updating resource group fair share configuration (GQL-aligned)."""

    resource_group_name: str = Field(description="Name of the resource group to update.")
    half_life_days: int | None | Unset = Field(
        default=UNSET,
        description="Half-life for exponential decay in days. Omit to leave unchanged.",
    )
    lookback_days: int | None | Unset = Field(
        default=UNSET,
        description="Total lookback period in days. Omit to leave unchanged.",
    )
    decay_unit_days: int | None | Unset = Field(
        default=UNSET,
        description="Granularity of decay buckets in days. Omit to leave unchanged.",
    )
    default_weight: Decimal | None | Unset = Field(
        default=UNSET,
        description="Default weight for entities. Omit to leave unchanged.",
    )
    resource_weights: list[ResourceWeightEntryInput] | None | Unset = Field(
        default=UNSET,
        description="Resource weights for fair share calculation. Omit to leave unchanged.",
    )


class UpdateResourceGroupConfigInput(BaseRequestModel):
    """Input for updating resource group configuration via GQL (all fields optional)."""

    resource_group_name: str = Field(description="Name of the resource group to update.")
    is_active: bool | None | Unset = Field(
        default=UNSET,
        description="Whether the resource group is active. Omit to leave unchanged.",
    )
    is_public: bool | None | Unset = Field(
        default=UNSET,
        description="Whether the resource group is public. Omit to leave unchanged.",
    )
    is_default: bool | None | Unset = Field(
        default=UNSET,
        description=(
            "Whether this is the default resource group. At most one resource group may hold"
            " the flag, so setting it to true is rejected while another one holds it; clear"
            " that one first. Omit to leave unchanged."
        ),
    )
    description: str | None | Unset = Field(
        default=UNSET,
        description="Human-readable description. Omit to leave unchanged; null clears.",
    )
    app_proxy_addr: str | None | Unset = Field(
        default=UNSET,
        description="App proxy address. Omit to leave unchanged; null clears.",
    )
    appproxy_api_token: str | None | Unset = Field(
        default=UNSET,
        description="App proxy API token. Omit to leave unchanged; null clears.",
    )
    use_host_network: bool | None | Unset = Field(
        default=UNSET,
        description="Whether to use host network mode. Omit to leave unchanged.",
    )
    scheduler_type: str | None | Unset = Field(
        default=UNSET,
        description="Scheduler type value (fifo/lifo/drf/fair-share). Omit to leave unchanged.",
    )
    preemption: PreemptionConfigInputDTO | None | Unset = Field(
        default=UNSET,
        description="Preemption configuration. Omit to leave unchanged.",
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


class ReplaceResourceGroupDefaultDeploymentOptionsInput(BaseRequestModel):
    """REST body for replacing a resource group's ``default_deployment_options``.

    Replace semantics — the supplied payload is the complete new value.
    Admin-only: future deployments created in this resource group will
    snapshot this new default. Existing deployments are not affected.
    """

    options: DeploymentOptionsInput = Field(
        description=(
            "New default deployment options payload. Replaces the existing"
            " default_deployment_options atomically."
        ),
    )


class ReplaceResourceGroupDefaultDeploymentOptionsGQLInput(BaseRequestModel):
    """GraphQL mutation input for replacing a resource group's ``default_deployment_options``.

    Mirrors :class:`ReplaceResourceGroupDefaultDeploymentOptionsInput`
    with the resource group name bundled in, since GQL mutations take a
    single input object.
    """

    resource_group_name: ResourceGroupName = Field(description="Target resource group name.")
    options: DeploymentOptionsInput = Field(
        description="New default deployment options payload.",
    )


class ReplaceResourceGroupDefaultSessionOptionsInput(BaseRequestModel):
    """REST body for replacing a resource group's ``default_session_options``.

    Replace semantics — the supplied payload is the complete new value.
    Admin-only: future sessions enqueued into this resource group will
    consult this new default via the scheduling controller's options
    resolver. Already-enqueued sessions are unaffected because they
    snapshot the old default at their own enqueue time.
    """

    options: DefaultSessionOptionsInput = Field(
        description=(
            "New default session options payload. Replaces the existing"
            " default_session_options atomically."
        ),
    )


class ReplaceResourceGroupDefaultSessionOptionsGQLInput(BaseRequestModel):
    """GraphQL mutation input for replacing a resource group's ``default_session_options``.

    Mirrors :class:`ReplaceResourceGroupDefaultSessionOptionsInput` with
    the resource group name bundled in, since GQL mutations take a
    single input object.
    """

    resource_group_name: ResourceGroupName = Field(description="Target resource group name.")
    options: DefaultSessionOptionsInput = Field(
        description="New default session options payload.",
    )

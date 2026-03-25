"""
Response DTOs for Agent v2 API.

Node models with nested sub-models mirroring GQL AgentV2GQL structure,
plus Payload models for search/detail/stats responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "AdminSearchAgentsPayload",
    "AgentNetworkInfo",
    "AgentNetworkInfoGQLDTO",
    "AgentNode",
    "AgentResourceGQLDTO",
    "AgentResourceInfo",
    "AgentResourceStatsPayload",
    "AgentStatsGQLDTO",
    "AgentStatusInfoGQLDTO",
    "AgentStatusInfo",
    "AgentSystemInfoGQLDTO",
    "AgentSystemInfo",
    "ComputePluginEntryDTO",
    "ComputePluginsGQLDTO",
    "GetAgentDetailPayload",
    "SearchAgentsPayload",
)


# ---------------------------------------------------------------------------
# Nested sub-models
# ---------------------------------------------------------------------------


class AgentResourceInfo(BaseResponseModel):
    """Hardware resource capacity, usage, and availability information."""

    capacity: dict[str, str] = Field(
        description=(
            "Total hardware resource capacity available on the agent. "
            "Expressed as a mapping of resource slot names to string quantities "
            "(e.g., cpu, mem, accelerators)."
        )
    )
    used: dict[str, str] = Field(
        description=(
            "Total amount of resources currently consumed by running and scheduled sessions. "
            "Expressed as a mapping with the same structure as capacity."
        )
    )
    free: dict[str, str] = Field(
        description=(
            "Available resources for scheduling new compute sessions (capacity - used). "
            "Expressed as a mapping with the same structure as capacity."
        )
    )


class AgentStatusInfo(BaseResponseModel):
    """Current operational status and lifecycle timestamps for an agent."""

    status: str = Field(
        description=(
            "Current operational status of the agent. One of: ALIVE, LOST, TERMINATED, RESTARTING."
        )
    )
    status_changed: datetime | None = Field(
        default=None,
        description="Timestamp when the agent last changed its status.",
    )
    first_contact: datetime | None = Field(
        default=None,
        description="Timestamp when the agent first registered with the manager.",
    )
    lost_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp when the agent was marked as lost or unreachable. "
            "Null if the agent has never been lost or is currently alive."
        ),
    )
    schedulable: bool = Field(
        description=(
            "Indicates whether the agent is available for scheduling new compute sessions. "
            "When false, no new sessions will be assigned to this agent."
        )
    )


class AgentSystemInfo(BaseResponseModel):
    """System configuration and software version information for an agent."""

    architecture: str = Field(
        description=(
            'Hardware architecture of the agent\'s host system (e.g., "x86_64", "aarch64"). '
            "Used to match compute sessions with compatible container images."
        )
    )
    version: str = Field(
        description=(
            "Version string of the Backend.AI agent software running on this node. "
            'Follows semantic versioning (e.g., "26.1.0").'
        )
    )
    auto_terminate_abusing_kernel: bool = Field(
        default=False,
        description="Legacy configuration flag, no longer actively used in the system.",
    )
    compute_plugins: ComputePluginsGQLDTO | None = Field(
        default=None,
        description=(
            "Compute plugin metadata supported by this agent. "
            "Each entry contains a plugin name and associated metadata."
        ),
    )


class AgentNetworkInfo(BaseResponseModel):
    """Network location and connectivity information for an agent."""

    region: str = Field(description="Logical region where the agent is deployed.")
    addr: str = Field(
        description=(
            'Network address and port where the agent can be reached (format: "host:port"). '
            "Used by the manager to communicate with the agent."
        )
    )


# ---------------------------------------------------------------------------
# Node model
# ---------------------------------------------------------------------------


class AgentNode(BaseResponseModel):
    """Node model representing an agent entity with nested information groups."""

    id: str = Field(description="Agent ID.")
    resource_info: AgentResourceInfo = Field(
        description="Hardware resource capacity, usage, and availability information."
    )
    status_info: AgentStatusInfo = Field(
        description="Current operational status and lifecycle timestamps."
    )
    system_info: AgentSystemInfo = Field(
        description="System configuration and software version information."
    )
    network_info: AgentNetworkInfo = Field(
        description="Network location and connectivity information."
    )
    scaling_group: str = Field(description="Scaling group this agent belongs to.")
    permissions: list[str] = Field(
        default_factory=list, description="Permission strings the caller has on this agent."
    )


# ---------------------------------------------------------------------------
# Payload models
# ---------------------------------------------------------------------------


class GetAgentDetailPayload(BaseResponseModel):
    """Payload for getting a single agent detail."""

    agent: AgentNode = Field(description="Agent detail data.")


class SearchAgentsPayload(BaseResponseModel):
    """Payload for paginated agent search results."""

    items: list[AgentNode] = Field(description="List of agent nodes.")
    pagination: PaginationInfo = Field(description="Pagination metadata.")


class AdminSearchAgentsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated agent search results."""

    items: list[AgentNode] = Field(description="List of agent nodes.")
    total_count: int = Field(description="Total number of agents matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class AgentResourceStatsPayload(BaseResponseModel):
    """Payload for aggregate resource statistics across agents."""

    total_used_slots: dict[str, str] = Field(
        description="Total resource slots currently in use across all agents."
    )
    total_free_slots: dict[str, str] = Field(
        description="Total resource slots available for scheduling across all agents."
    )
    total_capacity_slots: dict[str, str] = Field(
        description="Total hardware resource capacity across all agents."
    )


# ---------------------------------------------------------------------------
# GQL-specific DTOs (for @strawberry.experimental.pydantic.type conversion)
# These DTOs use JSON-compatible types (Any) for GQL JSON scalar fields,
# and str for enum fields that are converted at the GQL layer.
# ---------------------------------------------------------------------------


class AgentResourceGQLDTO(BaseResponseModel):
    """GQL-specific DTO for AgentResourceGQL.

    Uses Any for capacity/used/free to accommodate GQL JSON scalar type.
    """

    capacity: Any = Field(
        description=(
            "Total hardware resource capacity available on the agent. "
            "Expressed as a JSON object containing resource slots."
        )
    )
    used: Any = Field(
        description=(
            "Total amount of resources currently consumed by running and scheduled sessions."
        )
    )
    free: Any = Field(
        description="Available resources for scheduling new compute sessions (capacity - used)."
    )


class AgentStatusInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for AgentStatusInfoGQL.

    Uses str for status to accommodate internal AgentStatus enum conversion at GQL layer.
    """

    status: str = Field(
        description=(
            "Current operational status of the agent. One of: ALIVE, LOST, TERMINATED, RESTARTING."
        )
    )
    status_changed: datetime | None = Field(
        default=None,
        description="Timestamp when the agent last changed its status.",
    )
    first_contact: datetime | None = Field(
        default=None,
        description="Timestamp when the agent first registered with the manager.",
    )
    lost_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp when the agent was marked as lost or unreachable. "
            "Null if the agent has never been lost or is currently alive."
        ),
    )
    schedulable: bool = Field(
        description=(
            "Indicates whether the agent is available for scheduling new compute sessions."
        )
    )


class ComputePluginEntryDTO(BaseResponseModel):
    """DTO for a single compute plugin entry."""

    plugin_name: str = Field(
        description=(
            "Name of the compute plugin (e.g., 'cuda', 'rocm', 'tpu'). "
            "This identifier corresponds to the accelerator or resource type supported by the agent."
        )
    )
    value: str = Field(
        description=(
            "Plugin value string containing plugin-specific information. "
            "The content varies by plugin type and may include version or configuration details."
        )
    )


class ComputePluginsGQLDTO(BaseResponseModel):
    """GQL-specific DTO for ComputePluginsGQL.

    The entries field is typed as list[Any] because its GQL type
    (ComputePluginEntryGQL) is a nested GQL type declared explicitly on the GQL class.
    """

    entries: list[Any] = Field(
        description=("List of compute plugins. Each entry contains a plugin name and its metadata.")
    )


class AgentSystemInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for AgentSystemInfoGQL.

    compute_plugins is typed as Any because it is a nested GQL type (ComputePluginsGQL)
    declared explicitly on the GQL class.
    """

    architecture: str = Field(
        description=(
            'Hardware architecture of the agent\'s host system (e.g., "x86_64", "aarch64"). '
            "Used to match compute sessions with compatible container images."
        )
    )
    version: str = Field(
        description=(
            "Version string of the Backend.AI agent software running on this node. "
            'Follows semantic versioning (e.g., "26.1.0").'
        )
    )
    auto_terminate_abusing_kernel: bool = Field(
        description="Legacy configuration flag, no longer actively used in the system.",
    )
    compute_plugins: Any = Field(
        description=(
            "List of compute plugin metadata supported by this agent. "
            "Typed as Any because this field holds a nested GQL type (ComputePluginsGQL)."
        )
    )


class AgentNetworkInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for AgentNetworkInfoGQL (alias of AgentNetworkInfo for symmetry)."""

    region: str = Field(description="Logical region where the agent is deployed.")
    addr: str = Field(
        description=(
            'Network address and port where the agent can be reached (format: "host:port"). '
            "Used by the manager to communicate with the agent."
        )
    )


class AgentStatsGQLDTO(BaseResponseModel):
    """GQL-specific DTO for AgentStatsGQL.

    total_resource is typed as Any because it holds a nested GQL type (AgentResourceGQL)
    declared explicitly on the GQL class.
    """

    total_resource: Any = Field(
        description="Total hardware resource capacity, usage, and availability across all agents."
    )

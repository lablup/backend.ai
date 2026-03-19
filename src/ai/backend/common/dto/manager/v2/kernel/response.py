"""Response DTOs for kernel DTO v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchKernelsPayload",
    "KernelClusterInfo",
    "KernelClusterInfoGQLDTO",
    "KernelLifecycleInfo",
    "KernelLifecycleInfoGQLDTO",
    "KernelNetworkInfoGQLDTO",
    "KernelNode",
    "KernelResourceInfo",
    "KernelResourceInfoGQLDTO",
    "KernelSessionInfo",
    "KernelSessionInfoGQLDTO",
    "KernelUserInfo",
    "KernelUserInfoGQLDTO",
    "ResourceAllocationGQLDTO",
)


# ---------------------------------------------------------------------------
# Nested sub-models
# ---------------------------------------------------------------------------


class KernelSessionInfo(BaseResponseModel):
    """Information about the session this kernel belongs to."""

    session_id: UUID = Field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = Field(
        default=None, description="The creation ID used when creating the session."
    )
    name: str | None = Field(default=None, description="The name of the session.")
    session_type: str = Field(
        description="The type of session (interactive, batch, inference, system)."
    )


class KernelUserInfo(BaseResponseModel):
    """User and ownership information for a kernel."""

    user_uuid: UUID | None = Field(
        default=None, description="The UUID of the user who owns this kernel."
    )
    access_key: str | None = Field(
        default=None, description="The access key used to create this kernel."
    )
    domain_name: str | None = Field(default=None, description="The domain this kernel belongs to.")
    group_id: UUID | None = Field(
        default=None, description="The group (project) ID this kernel belongs to."
    )


class KernelClusterInfo(BaseResponseModel):
    """Cluster configuration for a kernel in distributed sessions."""

    cluster_mode: str = Field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = Field(description="Number of nodes in the cluster.")
    cluster_role: str = Field(
        description="The role of this kernel in the cluster (e.g., main, sub)."
    )
    cluster_idx: int = Field(description="The index of this kernel within the cluster (0-based).")
    local_rank: int = Field(description="The local rank of this kernel for distributed computing.")
    cluster_hostname: str = Field(
        description="The hostname assigned to this kernel within the cluster network."
    )


class KernelResourceInfo(BaseResponseModel):
    """Resource allocation information for a kernel."""

    scaling_group: str | None = Field(
        default=None,
        description="The resource group (scaling group) this kernel is assigned to.",
    )
    agent: str | None = Field(
        default=None,
        description="The ID of the agent running this kernel.",
    )
    agent_addr: str | None = Field(
        default=None, description="The address of the agent running this kernel."
    )
    container_id: str | None = Field(default=None, description="The container ID on the agent.")
    occupied_slots: dict[str, Any] | None = Field(
        default=None, description="The resource slots currently occupied by this kernel."
    )
    requested_slots: dict[str, Any] | None = Field(
        default=None, description="The resource slots originally requested for this kernel."
    )
    occupied_shares: dict[str, Any] | None = Field(
        default=None, description="The fractional resource shares occupied by this kernel."
    )
    resource_opts: dict[str, Any] | None = Field(
        default=None, description="Additional resource options and configurations for this kernel."
    )


class KernelLifecycleInfo(BaseResponseModel):
    """Lifecycle and status information for a kernel."""

    status: str = Field(
        description="Current status of the kernel (e.g., PENDING, RUNNING, TERMINATED)."
    )
    result: str = Field(
        description="The result of the kernel execution (UNDEFINED, SUCCESS, FAILURE)."
    )
    created_at: datetime | None = Field(
        default=None, description="Timestamp when the kernel was created."
    )
    terminated_at: datetime | None = Field(
        default=None, description="Timestamp when the kernel was terminated. Null if still active."
    )
    starts_at: datetime | None = Field(
        default=None, description="Scheduled start time for the kernel, if applicable."
    )
    status_info: str | None = Field(
        default=None, description="Additional status information or error message."
    )


# ---------------------------------------------------------------------------
# Main node model
# ---------------------------------------------------------------------------


class KernelNode(BaseResponseModel):
    """Node model representing a kernel (compute container) entity."""

    id: UUID = Field(description="Kernel ID.")
    startup_command: str | None = Field(
        default=None, description="Startup command executed when the kernel starts."
    )
    session: KernelSessionInfo = Field(
        description="Information about the session this kernel belongs to."
    )
    user: KernelUserInfo = Field(description="User and ownership information.")
    cluster: KernelClusterInfo = Field(
        description="Cluster configuration for distributed computing."
    )
    resource: KernelResourceInfo = Field(description="Resource allocation and agent information.")
    lifecycle: KernelLifecycleInfo = Field(description="Lifecycle status and timestamps.")


# ---------------------------------------------------------------------------
# Search / list response
# ---------------------------------------------------------------------------


class AdminSearchKernelsPayload(BaseResponseModel):
    """Payload for admin search of kernels."""

    items: list[KernelNode] = Field(description="List of kernel nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


# ---------------------------------------------------------------------------
# GQL-specific DTOs (for @strawberry.experimental.pydantic.type conversion)
# These DTOs use Any for nested GQL type fields and str for enum/internal-type
# fields that are converted at the GQL layer.
# ---------------------------------------------------------------------------


class KernelSessionInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2SessionInfoGQL.

    session_type is typed as str; enum (SessionTypes) conversion is done at GQL layer.
    """

    session_id: UUID = Field(
        description="The unique identifier of the session this kernel belongs to."
    )
    creation_id: str | None = Field(
        default=None, description="The creation ID used when creating the session."
    )
    name: str | None = Field(default=None, description="The name of the session.")
    session_type: str = Field(
        description="The type of session (interactive, batch, inference, system)."
    )


class KernelClusterInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2ClusterInfoGQL.

    Contains only the fields exposed by KernelV2ClusterInfoGQL (no cluster_mode/cluster_size).
    """

    cluster_role: str = Field(
        description="The role of this kernel in the cluster (e.g., main, sub)."
    )
    cluster_idx: int = Field(description="The index of this kernel within the cluster (0-based).")
    local_rank: int = Field(description="The local rank of this kernel for distributed computing.")
    cluster_hostname: str = Field(
        description="The hostname assigned to this kernel within the cluster network."
    )


class KernelUserInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2UserInfoGQL.

    user_id maps to user_uuid in KernelUserInfo.
    """

    user_id: UUID | None = Field(
        default=None, description="The UUID of the user who owns this kernel."
    )
    access_key: str | None = Field(
        default=None, description="The access key used to create this kernel."
    )
    domain_name: str | None = Field(default=None, description="The domain this kernel belongs to.")
    group_id: UUID | None = Field(
        default=None, description="The group (project) ID this kernel belongs to."
    )


class ResourceAllocationGQLDTO(BaseResponseModel):
    """GQL-specific DTO for ResourceAllocationGQL.

    requested and used are typed as Any because they hold nested GQL types (ResourceSlotGQL).
    """

    requested: Any = Field(
        description=(
            "The resource slots originally requested. "
            "Typed as Any because this field holds a nested GQL type (ResourceSlotGQL)."
        )
    )
    used: Any = Field(
        default=None,
        description=(
            "The resource slots currently used. "
            "Typed as Any because this field holds a nested GQL type (ResourceSlotGQL)."
        ),
    )


class KernelResourceInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2ResourceInfoGQL.

    allocation, shares, and resource_opts are typed as Any because they hold nested GQL types.
    """

    agent_id: str | None = Field(
        default=None,
        description="The ID of the agent running this kernel. Null if not yet assigned or hidden.",
    )
    resource_group_name: str | None = Field(
        default=None,
        description="The resource group (scaling group) this kernel is assigned to.",
    )
    container_id: str | None = Field(default=None, description="The container ID on the agent.")
    allocation: Any = Field(
        description=(
            "Resource allocation with requested and used slots. "
            "Typed as Any because this field holds a nested GQL type (ResourceAllocationGQL)."
        )
    )
    shares: Any = Field(
        description=(
            "The fractional resource shares occupied by this kernel. "
            "Typed as Any because this field holds a nested GQL type (ResourceSlotGQL)."
        )
    )
    resource_opts: Any = Field(
        default=None,
        description=(
            "Additional resource options and configurations. "
            "Typed as Any because this field holds a nested GQL type (ResourceOptsGQL)."
        ),
    )


class KernelNetworkInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2NetworkInfoGQL.

    service_ports is typed as Any because it holds a nested GQL type (ServicePortsGQL).
    """

    service_ports: Any = Field(
        default=None,
        description=(
            "Collection of service ports exposed by this kernel. "
            "Typed as Any because this field holds a nested GQL type (ServicePortsGQL)."
        ),
    )
    preopen_ports: list[int] | None = Field(
        default=None, description="List of ports that are pre-opened for this kernel."
    )


class KernelLifecycleInfoGQLDTO(BaseResponseModel):
    """GQL-specific DTO for KernelV2LifecycleInfoGQL.

    status and result are typed as str; enum conversion is done at the GQL layer.
    """

    status: str = Field(description="Current status of the kernel.")
    result: str = Field(description="The result of the kernel execution.")
    created_at: datetime | None = Field(
        default=None, description="Timestamp when the kernel was created."
    )
    terminated_at: datetime | None = Field(
        default=None, description="Timestamp when the kernel was terminated."
    )
    starts_at: datetime | None = Field(
        default=None, description="Scheduled start time for the kernel, if applicable."
    )

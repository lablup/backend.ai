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
    "KernelLifecycleInfo",
    "KernelNode",
    "KernelResourceInfo",
    "KernelSessionInfo",
    "KernelUserInfo",
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

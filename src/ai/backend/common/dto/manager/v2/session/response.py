"""
Response DTOs for Session v2 API.

Node models with nested sub-models and action Payload models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "AdminSearchSessionsPayload",
    "CommitSessionPayload",
    "DestroySessionPayload",
    "ExecutePayload",
    "RestartSessionPayload",
    "SearchSessionsPayload",
    "SessionLifecycleInfo",
    "SessionMetadataInfo",
    "SessionNetworkInfo",
    "SessionNode",
    "SessionResourceInfo",
    "SessionRuntimeInfo",
    "StartServicePayload",
)


# ---------------------------------------------------------------------------
# Nested sub-models
# ---------------------------------------------------------------------------


class SessionMetadataInfo(BaseResponseModel):
    """Metadata information for a session."""

    creation_id: str | None = Field(
        default=None,
        description="Server-generated unique token for tracking session creation.",
    )
    name: str | None = Field(default=None, description="Human-readable name of the session.")
    session_type: str = Field(description="Type of the session (interactive, batch, inference).")
    access_key: str | None = Field(
        default=None, description="Access key used to create this session."
    )
    cluster_mode: str = Field(
        description="Cluster mode for distributed sessions (single-node, multi-node)."
    )
    cluster_size: int = Field(description="Number of nodes in the cluster.")
    priority: int = Field(description="Scheduling priority of the session.")
    is_preemptible: bool = Field(
        description="Whether this session is eligible for preemption by higher-priority sessions."
    )
    tag: str | None = Field(default=None, description="Optional user-provided tag for the session.")


class SessionResourceInfo(BaseResponseModel):
    """Resource allocation information for a session."""

    occupying_slots: dict[str, Any] | None = Field(
        default=None, description="Currently occupied resource slots."
    )
    requested_slots: dict[str, Any] | None = Field(
        default=None, description="Resource slots requested at session creation."
    )
    scaling_group_name: str | None = Field(
        default=None,
        description="The resource group (scaling group) this session is assigned to.",
    )
    target_sgroup_names: list[str] | None = Field(
        default=None,
        description="Candidate resource group names considered during scheduling.",
    )
    agent_ids: list[str] | None = Field(
        default=None, description="IDs of agents running this session's kernels."
    )
    images: list[str] | None = Field(
        default=None, description="Container images used by this session."
    )


class SessionLifecycleInfo(BaseResponseModel):
    """Lifecycle status and timestamps for a session."""

    status: str = Field(description="Current status of the session.")
    result: str = Field(description="Result of the session execution (success, failure, etc.).")
    created_at: datetime | None = Field(
        default=None, description="Timestamp when the session was created."
    )
    terminated_at: datetime | None = Field(
        default=None,
        description="Timestamp when the session was terminated. Null if still active.",
    )
    starts_at: datetime | None = Field(
        default=None, description="Scheduled start time for the session, if applicable."
    )
    batch_timeout: int | None = Field(
        default=None,
        description="Batch execution timeout in seconds. Applicable to batch sessions.",
    )
    status_info: str | None = Field(
        default=None, description="Additional status information or error message."
    )


class SessionRuntimeInfo(BaseResponseModel):
    """Runtime execution configuration for a session."""

    environ: dict[str, str] | None = Field(
        default=None, description="Environment variables for the session."
    )
    bootstrap_script: str | None = Field(
        default=None, description="Bootstrap script to run before the main process."
    )
    startup_command: str | None = Field(
        default=None, description="Startup command to execute when the session starts."
    )
    callback_url: str | None = Field(
        default=None,
        description="URL to call back when the session completes (e.g., for batch sessions).",
    )


class SessionNetworkInfo(BaseResponseModel):
    """Network configuration for a session."""

    use_host_network: bool = Field(
        description="Whether the session uses the host network directly."
    )
    network_type: str | None = Field(
        default=None, description="Type of network used by the session."
    )
    network_id: str | None = Field(default=None, description="ID of the network if applicable.")


# ---------------------------------------------------------------------------
# Main node model
# ---------------------------------------------------------------------------


class SessionNode(BaseResponseModel):
    """Node model representing a session entity with nested info sub-models."""

    id: UUID = Field(description="Session ID.")
    metadata: SessionMetadataInfo = Field(
        description="Metadata including name, type, and cluster information."
    )
    resource: SessionResourceInfo = Field(
        description="Resource allocation and cluster information."
    )
    lifecycle: SessionLifecycleInfo = Field(description="Lifecycle status and timestamps.")
    runtime: SessionRuntimeInfo = Field(description="Runtime execution configuration.")
    network: SessionNetworkInfo = Field(description="Network configuration.")


# ---------------------------------------------------------------------------
# Action Payload models
# ---------------------------------------------------------------------------


class RestartSessionPayload(BaseResponseModel):
    """Payload for session restart action (204 No Content in practice)."""


class DestroySessionPayload(BaseResponseModel):
    """Payload for session destroy action result."""

    result: dict[str, Any] = Field(description="Destroy action result details.")


class CommitSessionPayload(BaseResponseModel):
    """Payload for session commit (imagify) action result."""

    result: dict[str, Any] = Field(description="Commit action result details.")


class ExecutePayload(BaseResponseModel):
    """Payload for code execution action result."""

    result: dict[str, Any] = Field(description="Execution result details.")


class StartServicePayload(BaseResponseModel):
    """Payload for start service (app proxy) action result."""

    token: str = Field(description="Authentication token for the service proxy.")
    wsproxy_addr: str = Field(description="WebSocket proxy address for the service.")


# ---------------------------------------------------------------------------
# Search / list response
# ---------------------------------------------------------------------------


class SearchSessionsPayload(BaseResponseModel):
    """Payload for paginated session search results."""

    items: list[SessionNode] = Field(description="List of session nodes.")
    pagination: PaginationInfo = Field(description="Pagination metadata.")


class AdminSearchSessionsPayload(BaseResponseModel):
    """Payload for admin search of sessions."""

    items: list[SessionNode] = Field(description="List of session nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")

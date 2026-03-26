"""
Request DTOs for Session v2 API.

Input models for session search, lifecycle actions, and service management.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.session.types import (
    ClusterModeEnum,
    CreateSessionTypeEnum,
    OrderDirection,
    SessionOrderField,
    SessionStatusFilter,
)

__all__ = (
    "AdminSearchSessionsInput",
    "BatchConfigInput",
    "CommitSessionInput",
    "EnqueueSessionInput",
    "DestroySessionInput",
    "DownloadFilesInput",
    "ExecuteInput",
    "GetContainerLogsInput",
    "GetSessionLogsQuery",
    "ListFilesInput",
    "MountItemInput",
    "RenameSessionInput",
    "ResourceOptsInput",
    "ResourceSlotEntryInput",
    "RestartSessionInput",
    "SearchSessionsInput",
    "SessionFilter",
    "SessionIdPathParam",
    "SessionOrder",
    "SessionPathParam",
    "ShutdownServiceInput",
    "ShutdownSessionServiceInput",
    "StartServiceInput",
    "StartSessionServiceInput",
    "TerminateSessionsInput",
    "UpdateSessionInput",
    "UploadFilesInput",
)


# ---------------------------------------------------------------------------
# Path parameter
# ---------------------------------------------------------------------------


class SessionPathParam(BaseRequestModel):
    """Path parameter for session-scoped endpoints."""

    session_name: str


class SessionIdPathParam(BaseRequestModel):
    """Path parameter for session ID-based endpoints."""

    session_id: UUID


# ---------------------------------------------------------------------------
# Search / query
# ---------------------------------------------------------------------------


class SessionFilter(BaseRequestModel):
    """Filter criteria for session listing."""

    id: UUIDFilter | None = None
    status: SessionStatusFilter | None = None
    name: StringFilter | None = None
    domain_name: StringFilter | None = None
    project_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None
    created_at: DateTimeRangeFilter | None = None
    AND: list[SessionFilter] | None = None
    OR: list[SessionFilter] | None = None
    NOT: list[SessionFilter] | None = None


SessionFilter.model_rebuild()


class SessionOrder(BaseRequestModel):
    """Ordering specification for session listing."""

    field: SessionOrderField
    direction: OrderDirection


class SearchSessionsInput(BaseRequestModel):
    """Input for paginated session search."""

    filter: SessionFilter | None = None
    order: SessionOrder | None = None
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)


class AdminSearchSessionsInput(BaseRequestModel):
    """Input for admin search of sessions with cursor and offset pagination."""

    filter: SessionFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


class RestartSessionInput(BaseRequestModel):
    """Input for restarting a session."""

    owner_access_key: str | None = None


class DestroySessionInput(BaseRequestModel):
    """Input for destroying a session."""

    forced: bool = False
    recursive: bool = False
    owner_access_key: str | None = None


# ---------------------------------------------------------------------------
# Commit / imagify
# ---------------------------------------------------------------------------


class CommitSessionInput(BaseRequestModel):
    """Input for committing a session to an image snapshot."""

    login_session_token: str | None = None
    filename: str | None = None


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------


class ExecuteInput(BaseRequestModel):
    """Input for executing code in a session kernel."""

    mode: str | None = None
    run_id: str | None = None
    code: str | None = None
    options: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Service management
# ---------------------------------------------------------------------------


class StartServiceInput(BaseRequestModel):
    """Input for starting an app service within a session."""

    app: str
    port: int | None = Field(default=None, ge=1024, le=65535)
    envs: str | None = None
    arguments: str | None = None
    login_session_token: str | None = None


class ShutdownServiceInput(BaseRequestModel):
    """Input for shutting down an app service within a session."""

    service_name: str


# ---------------------------------------------------------------------------
# Session rename
# ---------------------------------------------------------------------------


class RenameSessionInput(BaseRequestModel):
    """Input for renaming a session."""

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


class DownloadFilesInput(BaseRequestModel):
    """Input for downloading files from a session."""

    files: list[str]


class UploadFilesInput(BaseRequestModel):
    """Input for uploading files to a session (multipart body; path param only)."""


class ListFilesInput(BaseRequestModel):
    """Input for listing files in a session."""

    path: str = "."


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


class GetContainerLogsInput(BaseRequestModel):
    """Input for retrieving container logs from a session."""

    owner_access_key: str | None = None
    kernel_id: UUID | None = None


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------


class ResourceOptsInput(BaseRequestModel):
    """Additional resource options."""

    shmem: str | None = Field(default=None, description="Shared memory size (e.g., '1g').")


class MountItemInput(BaseRequestModel):
    """A single virtual folder mount specification."""

    vfolder_id: UUID = Field(description="Virtual folder UUID to mount.")
    mount_path: str | None = Field(
        default=None, description="Custom mount path. Uses default path if omitted."
    )
    permission: str | None = Field(
        default=None, description="Mount permission override ('rw' or 'ro')."
    )


class BatchConfigInput(BaseRequestModel):
    """Batch session specific configuration. Required when session_type is BATCH."""

    startup_command: str = Field(description="Shell command to execute.", min_length=1)
    starts_at: str | None = Field(
        default=None, description="Scheduled start time in ISO 8601 format."
    )
    batch_timeout: int | None = Field(
        default=None, ge=0, description="Execution timeout in seconds."
    )


class EnqueueSessionInput(BaseRequestModel):
    """Input for enqueuing a new compute session (interactive or batch)."""

    session_name: str = Field(
        description="Session name. Must be unique per user among active sessions.",
        min_length=1,
        max_length=64,
    )
    session_type: CreateSessionTypeEnum = Field(
        description="Session type. Only INTERACTIVE and BATCH are user-creatable.",
    )
    image_id: UUID = Field(description="Image UUID to use for the session.")

    # Resource
    resource_entries: list[ResourceSlotEntryInput] = Field(
        description="Resource slot allocations.",
    )
    resource_group: str | None = Field(
        default=None, description="Scaling group name. Auto-selected if omitted."
    )
    resource_opts: ResourceOptsInput | None = Field(
        default=None, description="Additional resource options."
    )
    cluster_mode: ClusterModeEnum = Field(
        default=ClusterModeEnum.SINGLE_NODE, description="Cluster networking mode."
    )
    cluster_size: int = Field(default=1, ge=1, description="Number of containers in the session.")

    # Storage
    mounts: list[MountItemInput] | None = Field(
        default=None, description="Virtual folder mount specifications."
    )

    # Execution
    environ: dict[str, str] | None = Field(
        default=None, description="Environment variables injected into the container."
    )
    preopen_ports: list[int] | None = Field(
        default=None, description="Ports to pre-open for services (e.g., [8080, 8888])."
    )
    bootstrap_script: str | None = Field(
        default=None,
        description="Shell script executed on container startup. Falls back to keypair setting.",
    )

    # Scheduling
    priority: int = Field(default=10, ge=0, le=100, description="Scheduling priority (0-100).")
    is_preemptible: bool = Field(default=True, description="Whether this session can be preempted.")
    dependencies: list[UUID] | None = Field(
        default=None, description="Session IDs that must complete before this session starts."
    )
    agent_list: list[str] | None = Field(
        default=None, description="Designated agent IDs for placement constraint."
    )
    attach_network: UUID | None = Field(
        default=None, description="Persistent network UUID to attach."
    )

    # Metadata
    tag: str | None = Field(default=None, max_length=64, description="User-defined tag.")
    callback_url: str | None = Field(
        default=None, description="Webhook URL for session lifecycle events."
    )

    # Batch-only
    batch: BatchConfigInput | None = Field(
        default=None,
        description="Batch configuration. Required for BATCH, rejected for INTERACTIVE.",
    )

    # Project scope
    project_id: UUID = Field(description="Project (group) UUID.")


# ---------------------------------------------------------------------------
# Terminate (batch)
# ---------------------------------------------------------------------------


class TerminateSessionsInput(BaseRequestModel):
    """Input for terminating one or more sessions."""

    session_ids: list[UUID] = Field(description="Session UUIDs to terminate.")
    forced: bool = Field(default=False, description="Force-terminate without waiting for cleanup.")


# ---------------------------------------------------------------------------
# Service management (v2 typed)
# ---------------------------------------------------------------------------


class StartSessionServiceInput(BaseRequestModel):
    """Input for starting an app service within a session."""

    service: str = Field(description="Service name (e.g., 'jupyter', 'vscode', 'tensorboard').")
    port: int | None = Field(
        default=None, ge=1024, le=65535, description="Specific container port."
    )
    envs: dict[str, str] | None = Field(
        default=None, description="Environment variables for the service."
    )
    arguments: dict[str, str] | None = Field(
        default=None, description="Arguments passed to the service."
    )
    login_session_token: str | None = Field(
        default=None, description="Login session token for proxy auth."
    )


class ShutdownSessionServiceInput(BaseRequestModel):
    """Input for shutting down a service in a session."""

    service: str = Field(description="Service name to shut down.")


# ---------------------------------------------------------------------------
# Logs query
# ---------------------------------------------------------------------------


class GetSessionLogsQuery(BaseRequestModel):
    """Query parameters for getting session logs."""

    kernel_id: UUID | None = Field(
        default=None, description="Specific kernel UUID. Main kernel if omitted."
    )


# ---------------------------------------------------------------------------
# Update session
# ---------------------------------------------------------------------------


class UpdateSessionInput(BaseRequestModel):
    """Input for updating a session."""

    name: str | None = Field(
        default=None, min_length=1, max_length=64, description="New session name."
    )
    tag: str | None = Field(default=None, max_length=64, description="Updated tag.")

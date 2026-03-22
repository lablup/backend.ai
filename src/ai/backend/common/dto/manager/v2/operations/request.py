"""
Request DTOs for operations DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)

__all__ = (
    "AppendErrorLogInput",
    "ClearErrorLogInput",
    "ListErrorLogsInput",
    "PerformSchedulerOpsInput",
    "SubscribeBackgroundTaskInput",
    "SubscribeSessionEventsInput",
    "UpdateAnnouncementInput",
    "UpdateManagerStatusInput",
)


class AppendErrorLogInput(BaseRequestModel):
    """Input for appending an error log entry."""

    severity: ErrorLogSeverity = Field(
        description="Severity level of the error log (critical, error, warning)",
    )
    source: str = Field(
        description="Source component or module that generated the error",
    )
    message: str = Field(
        description="Human-readable error message",
    )
    context_lang: str = Field(
        description="Programming language context of the error",
    )
    context_env: str = Field(
        description="JSON-encoded environment context of the error",
    )
    request_url: str | None = Field(
        default=None,
        description="URL of the request that triggered the error, if applicable",
    )
    request_status: int | None = Field(
        default=None,
        description="HTTP status code of the request that triggered the error, if applicable",
    )
    traceback: str | None = Field(
        default=None,
        description="Stack trace of the error, if available",
    )


class ListErrorLogsInput(BaseRequestModel):
    """Input for listing error logs with pagination."""

    mark_read: bool = Field(
        default=False,
        description="Whether to mark the returned logs as read",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of log entries per page",
    )
    page_no: int = Field(
        default=1,
        ge=1,
        description="Page number to retrieve (1-indexed)",
    )


class ClearErrorLogInput(BaseRequestModel):
    """Input for clearing an error log entry."""

    log_id: UUID = Field(
        description="UUID of the error log entry to mark as cleared",
    )


class UpdateManagerStatusInput(BaseRequestModel):
    """Input for updating the manager status."""

    status: ManagerStatus = Field(
        description="Target manager status",
    )
    force_kill: bool = Field(
        default=False,
        description="Whether to force-kill all running sessions during status transition",
    )


class UpdateAnnouncementInput(BaseRequestModel):
    """Input for updating the system announcement."""

    enabled: bool = Field(
        default=False,
        description="Whether the announcement is enabled",
    )
    message: str | None = Field(
        default=None,
        description="Announcement message text; required when enabled is true",
    )


class PerformSchedulerOpsInput(BaseRequestModel):
    """Input for performing a scheduler operation."""

    op: SchedulerOps = Field(
        description="Scheduler operation to perform",
    )
    args: list[str] = Field(
        description="List of agent IDs to include or exclude from scheduling",
    )


class SubscribeSessionEventsInput(BaseRequestModel):
    """Input for subscribing to session event streams (SSE)."""

    session_name: str = Field(
        default="*",
        description="Session name to filter events for; '*' for all sessions",
    )
    owner_access_key: str | None = Field(
        default=None,
        description="Access key of the session owner; defaults to the requester's key",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session UUID to filter events for; overrides session_name if set",
    )
    group_name: str = Field(
        default="*",
        description="Group name to filter events for; '*' for all groups",
    )
    scope: str = Field(
        default="*",
        description="Comma-separated event scopes (e.g., 'session,kernel'); '*' for all",
    )


class SubscribeBackgroundTaskInput(BaseRequestModel):
    """Input for subscribing to background task event streams (SSE)."""

    task_id: UUID = Field(
        description="UUID of the background task to monitor",
    )

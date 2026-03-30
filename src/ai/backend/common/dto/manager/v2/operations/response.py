"""
Response DTOs for operations DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogContextInfo,
    ErrorLogRequestInfo,
)

__all__ = (
    "AnnouncementNode",
    "AppendErrorLogPayload",
    "ClearErrorLogPayload",
    "ErrorLogNode",
    "ListErrorLogsPayload",
    "ManagerNodeInfo",
    "ManagerStatusPayload",
)


class ErrorLogNode(BaseResponseModel):
    """Node model representing an error log entry with nested context and request info."""

    log_id: str = Field(
        description="UUID of the error log entry, serialized as a string",
    )
    created_at: float = Field(
        description="Unix timestamp of when the log entry was created",
    )
    severity: str = Field(
        description="Severity level (critical, error, warning)",
    )
    source: str = Field(
        description="Source component or module that generated the error",
    )
    user: str | None = Field(
        description="UUID of the user who generated the error, serialized as a string",
    )
    is_read: bool = Field(
        description="Whether the log entry has been read",
    )
    message: str = Field(
        description="Human-readable error message",
    )
    context: ErrorLogContextInfo = Field(
        description="Context information for the error (language and environment)",
    )
    request: ErrorLogRequestInfo = Field(
        description="Request information for the error (URL and status code)",
    )
    traceback: str | None = Field(
        default=None,
        description="Stack trace of the error, if available",
    )
    is_cleared: bool | None = Field(
        default=None,
        description="Whether the log entry has been cleared (only present for admin users)",
    )


class AppendErrorLogPayload(BaseResponseModel):
    """Payload for error log append mutation result."""

    success: bool = Field(
        description="Whether the log entry was created successfully",
    )


class ListErrorLogsPayload(BaseResponseModel):
    """Payload containing a paginated list of error logs."""

    logs: list[ErrorLogNode] = Field(
        description="List of error log entries",
    )
    count: int = Field(
        description="Total number of error log entries matching the query",
    )


class ClearErrorLogPayload(BaseResponseModel):
    """Payload for error log clear mutation result."""

    success: bool = Field(
        description="Whether the log entry was cleared successfully",
    )


class ManagerNodeInfo(BaseResponseModel):
    """Information about a single manager node."""

    id: str = Field(
        description="Manager node identifier (hostname or configured ID)",
    )
    num_proc: int = Field(
        description="Number of worker processes for the manager node",
    )
    service_addr: str = Field(
        description="Service address of the manager node",
    )
    heartbeat_timeout: float = Field(
        description="Heartbeat timeout in seconds",
    )
    ssl_enabled: bool = Field(
        description="Whether SSL is enabled for the manager node",
    )
    active_sessions: int = Field(
        description="Number of currently active sessions on the node",
    )
    status: str = Field(
        description="Current manager status (running, frozen)",
    )
    version: str = Field(
        description="Manager software version string",
    )
    api_version: list[int | str] = Field(
        description="Current API version as [major, revision_date] (e.g. [9, '20250722'])",
    )


class ManagerStatusPayload(BaseResponseModel):
    """Payload containing manager cluster status information."""

    nodes: list[ManagerNodeInfo] = Field(
        description="List of manager nodes in the cluster",
    )
    status: str = Field(
        description="Overall cluster manager status",
    )
    active_sessions: int = Field(
        description="Total number of active sessions across all nodes",
    )


class AnnouncementNode(BaseResponseModel):
    """Node model representing the system announcement."""

    enabled: bool = Field(
        description="Whether the announcement is currently enabled",
    )
    message: str = Field(
        description="Announcement message text; empty string if disabled",
    )

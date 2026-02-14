"""
Response DTOs for operations system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseFieldModel, BaseResponseModel

__all__ = (
    "AppendErrorLogResponse",
    "ClearErrorLogResponse",
    "ErrorLogItem",
    "FetchManagerStatusResponse",
    "GetAnnouncementResponse",
    "ListErrorLogsResponse",
    "ManagerNodeInfo",
)


# -------- Logs --------


class ErrorLogItem(BaseFieldModel):
    """Individual error log entry returned in list responses."""

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
    context_lang: str = Field(
        description="Programming language context of the error",
    )
    context_env: dict[str, Any] = Field(
        description="Environment context of the error",
    )
    request_url: str | None = Field(
        description="URL of the request that triggered the error, if applicable",
    )
    request_status: int | None = Field(
        description="HTTP status code of the request, if applicable",
    )
    traceback: str | None = Field(
        description="Stack trace of the error, if available",
    )
    is_cleared: bool | None = Field(
        default=None,
        description="Whether the log entry has been cleared (only present for admin users)",
    )


class AppendErrorLogResponse(BaseResponseModel):
    """Response for a successful error log creation."""

    success: bool = Field(
        description="Whether the log entry was created successfully",
    )


class ListErrorLogsResponse(BaseResponseModel):
    """Response containing a paginated list of error logs."""

    logs: list[ErrorLogItem] = Field(
        description="List of error log entries",
    )
    count: int = Field(
        description="Total number of error log entries matching the query",
    )


class ClearErrorLogResponse(BaseResponseModel):
    """Response for a successful error log clear operation."""

    success: bool = Field(
        description="Whether the log entry was cleared successfully",
    )


# -------- Manager --------


class ManagerNodeInfo(BaseFieldModel):
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
    api_version: int = Field(
        description="Current API version served by the manager",
    )


class FetchManagerStatusResponse(BaseResponseModel):
    """Response containing manager cluster status information."""

    nodes: list[ManagerNodeInfo] = Field(
        description="List of manager nodes in the cluster",
    )
    status: str = Field(
        description="Overall cluster manager status",
    )
    active_sessions: int = Field(
        description="Total number of active sessions across all nodes",
    )


class GetAnnouncementResponse(BaseResponseModel):
    """Response containing the current system announcement."""

    enabled: bool = Field(
        description="Whether the announcement is currently enabled",
    )
    message: str = Field(
        description="Announcement message text; empty string if disabled",
    )

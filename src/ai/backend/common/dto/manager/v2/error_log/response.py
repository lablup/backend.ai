"""
Response DTOs for error_log DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import ErrorLogContextInfo, ErrorLogRequestInfo

__all__ = (
    "AppendErrorLogPayload",
    "ErrorLogNode",
    "ListErrorLogsPayload",
    "MarkClearedPayload",
)


class ErrorLogNode(BaseResponseModel):
    """Node model representing a single error log entry."""

    log_id: str = Field(description="Error log ID")
    created_at: float = Field(description="Creation timestamp (Unix epoch float)")
    severity: str = Field(description="Log severity level")
    source: str = Field(description="Source service or component that generated the error")
    user: str | None = Field(default=None, description="UUID of the user who triggered the error")
    is_read: bool = Field(description="Whether the log has been read")
    message: str = Field(description="Error message")
    context: ErrorLogContextInfo = Field(description="Language and environment context")
    request_info: ErrorLogRequestInfo = Field(description="HTTP request details")
    traceback: str | None = Field(default=None, description="Traceback string")
    is_cleared: bool | None = Field(
        default=None, description="Whether the log has been cleared (admin only)"
    )


class AppendErrorLogPayload(BaseResponseModel):
    """Payload for error log append mutation result."""

    success: bool = Field(description="Whether the operation succeeded")


class ListErrorLogsPayload(BaseResponseModel):
    """Payload for error log list query result."""

    logs: list[ErrorLogNode] = Field(description="List of error log entries")
    count: int = Field(description="Total count of matching error logs")


class MarkClearedPayload(BaseResponseModel):
    """Payload for mark-cleared mutation result."""

    success: bool = Field(description="Whether the operation succeeded")

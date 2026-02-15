"""
Response DTOs for error log management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ErrorLogDTO",
    "AppendErrorLogResponse",
    "ListErrorLogsResponse",
    "MarkClearedResponse",
)


class ErrorLogDTO(BaseModel):
    """DTO representing a single error log entry."""

    log_id: str = Field(description="Error log ID")
    created_at: float = Field(description="Creation timestamp")
    severity: str = Field(description="Log severity level")
    source: str = Field(description="Source of the error")
    user: str | None = Field(default=None, description="User UUID who triggered the error")
    is_read: bool = Field(description="Whether the log has been read")
    message: str = Field(description="Error message")
    context_lang: str = Field(description="Language context")
    context_env: dict[str, Any] = Field(description="Environment context")
    request_url: str | None = Field(default=None, description="URL of the failed request")
    request_status: int | None = Field(
        default=None, description="HTTP status code of the failed request"
    )
    traceback: str | None = Field(default=None, description="Traceback string")
    is_cleared: bool | None = Field(
        default=None, description="Whether the log has been cleared (admin only)"
    )


class AppendErrorLogResponse(BaseResponseModel):
    """Response for appending an error log entry."""

    success: bool = Field(description="Whether the operation succeeded")


class ListErrorLogsResponse(BaseResponseModel):
    """Response for listing error logs."""

    logs: list[ErrorLogDTO] = Field(description="List of error log entries")
    count: int = Field(description="Total count of matching error logs")


class MarkClearedResponse(BaseResponseModel):
    """Response for marking an error log as cleared."""

    success: bool = Field(description="Whether the operation succeeded")

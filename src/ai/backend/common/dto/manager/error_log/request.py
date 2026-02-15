"""
Request DTOs for error log management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "AppendErrorLogRequest",
    "ListErrorLogsRequest",
)


class AppendErrorLogRequest(BaseRequestModel):
    """Request body for appending a new error log entry."""

    severity: str = Field(description="Log severity level (critical, error, warning)")
    source: str = Field(description="Source of the error")
    message: str = Field(description="Error message")
    context_lang: str = Field(description="Language context")
    context_env: dict[str, Any] = Field(description="Environment context as JSON object")
    request_url: str | None = Field(
        default=None, description="URL of the request that caused the error"
    )
    request_status: int | None = Field(
        default=None, description="HTTP status code of the failed request"
    )
    traceback: str | None = Field(default=None, description="Traceback string")


class ListErrorLogsRequest(BaseRequestModel):
    """Request parameters for listing error logs."""

    mark_read: bool = Field(default=False, description="Mark listed logs as read")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of logs per page")
    page_no: int = Field(default=1, ge=1, description="Page number")

"""
Common types for error_log DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ErrorLogContextInfo",
    "ErrorLogRequestInfo",
)


class ErrorLogContextInfo(BaseResponseModel):
    """Semantic grouping of context fields for an error log entry."""

    context_lang: str = Field(description="Language context of the error")
    context_env: dict[str, Any] = Field(description="Environment context as a JSON object")


class ErrorLogRequestInfo(BaseResponseModel):
    """Semantic grouping of HTTP request fields for an error log entry."""

    request_url: str | None = Field(
        default=None, description="URL of the request that caused the error"
    )
    request_status: int | None = Field(
        default=None, description="HTTP status code of the failed request"
    )

"""
Common types for operations DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.operations.types import (
    ErrorLogSeverity,
    ManagerStatus,
    SchedulerOps,
)

__all__ = (
    "ErrorLogContextInfo",
    "ErrorLogOrderField",
    "ErrorLogRequestInfo",
    "ErrorLogSeverity",
    "ManagerStatus",
    "OrderDirection",
    "SchedulerOps",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ErrorLogOrderField(StrEnum):
    """Fields available for ordering error logs."""

    CREATED_AT = "created_at"
    SEVERITY = "severity"
    SOURCE = "source"


class ErrorLogContextInfo(BaseResponseModel):
    """Context information for error log entries."""

    lang: str = Field(description="Programming language context of the error")
    env: dict[str, Any] = Field(description="Environment context of the error")


class ErrorLogRequestInfo(BaseResponseModel):
    """Request information for error log entries."""

    url: str | None = Field(
        default=None,
        description="URL of the request that triggered the error",
    )
    status: int | None = Field(
        default=None,
        description="HTTP status code of the request",
    )

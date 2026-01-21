from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class ErrorLogSeverity(enum.StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ErrorLogMeta:
    created_at: datetime
    user: uuid.UUID | None
    source: str
    is_read: bool
    is_cleared: bool
    context_lang: str
    context_env: dict[str, Any]
    request_url: str | None
    request_status: int | None


@dataclass
class ErrorLogContent:
    severity: ErrorLogSeverity
    message: str
    traceback: str | None


@dataclass
class ErrorLogData:
    id: uuid.UUID
    meta: ErrorLogMeta
    content: ErrorLogContent


@dataclass
class ErrorLogListResult:
    """Search result with total count and pagination info for error logs."""

    items: list[ErrorLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

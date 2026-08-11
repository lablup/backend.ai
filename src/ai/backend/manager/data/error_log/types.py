from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.error_log import ErrorLogID


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
class ErrorLogData(EntityData):
    id: ErrorLogID
    meta: ErrorLogMeta
    content: ErrorLogContent

    @override
    def entity_id(self) -> EntityID:
        return self.id


@dataclass
class ErrorLogListResult:
    """Search result with total count and pagination info for error logs."""

    items: list[ErrorLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

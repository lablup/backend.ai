from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.error_log import ErrorLogID
from ai.backend.common.data.entity.types import EntityIdentifier, FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.common import ObjectNotFound


class ErrorLogSeverity(enum.StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ErrorLogMeta:
    created_at: datetime
    user: UserID | None
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
class ErrorLogData(FieldData):
    """One recorded error, read through the user it happened to."""

    id: ErrorLogID
    meta: ErrorLogMeta
    content: ErrorLogContent

    @override
    def owner_entity_id(self) -> EntityIdentifier:
        """The user the error was recorded against.

        Rows written before logs became a user's field carry no user; the column
        stays nullable for them, and they have no owner to be read through.
        """
        if self.meta.user is None:
            raise ObjectNotFound(object_name="error log owner")
        return self.meta.user


@dataclass
class ErrorLogListResult:
    """Search result with total count and pagination info for error logs."""

    items: list[ErrorLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

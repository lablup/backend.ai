from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.manager.data.error_log.types import ErrorLogSeverity
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = ("ErrorLogCreatorSpec",)


@dataclass
class ErrorLogCreatorSpec(CreatorSpec[ErrorLogRow]):
    severity: ErrorLogSeverity
    source: str
    message: str
    context_lang: str
    context_env: dict[str, Any]
    user: uuid.UUID | None = None
    is_read: bool = False
    is_cleared: bool = False
    request_url: str | None = None
    request_status: int | None = None
    traceback: str | None = None
    created_at: datetime | None = None

    @override
    def build_row(self) -> ErrorLogRow:
        return ErrorLogRow(
            severity=self.severity,
            source=self.source,
            message=self.message,
            context_lang=self.context_lang,
            context_env=self.context_env,
            user=self.user,
            is_read=self.is_read,
            is_cleared=self.is_cleared,
            request_url=self.request_url,
            request_status=self.request_status,
            traceback=self.traceback,
            created_at=self.created_at,
        )

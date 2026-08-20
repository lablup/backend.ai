"""Write specs for error logs.

The row itself still lives in the legacy flat ``models/error_logs.py``; this package
holds only what the v2 lineage requires to sit under ``models/``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogSeverity
from ai.backend.manager.models.error_log.row import ErrorLogRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ErrorLogCreator(FieldCreator[UserID, ErrorLogRow, ErrorLogData]):
    """Creator for one recorded error, written under the user it happened to."""

    severity: ErrorLogSeverity
    source: str
    message: str
    context_lang: str
    context_env: dict[str, Any]
    is_read: bool = False
    is_cleared: bool = False
    request_url: str | None = None
    request_status: int | None = None
    traceback: str | None = None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: UserID) -> ErrorLogRow:
        return ErrorLogRow(
            severity=self.severity.value,
            source=self.source,
            message=self.message,
            context_lang=self.context_lang,
            context_env=self.context_env,
            user=owner_id,
            is_read=self.is_read,
            is_cleared=self.is_cleared,
            request_url=self.request_url,
            request_status=self.request_status,
            traceback=self.traceback,
        )

    @override
    def to_data(self, row: ErrorLogRow) -> ErrorLogData:
        return row.to_dataclass()

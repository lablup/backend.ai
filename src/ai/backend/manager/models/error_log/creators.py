"""Write specs for error logs.

The row itself still lives in the legacy flat ``models/error_logs.py``; this package
holds only what the v2 lineage requires to sit under ``models/``.
"""

from __future__ import annotations

import uuid
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.error_log import ERROR_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import ScopeRef, ScopeType
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.data.error_log.types import ErrorLogData, ErrorLogSeverity
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

_ERROR_LOG_SCOPE = ScopeType(ERROR_LOG_ENTITY_TYPE)


@dataclass
class ErrorLogCreator(EntityCreator[ErrorLogRow, ErrorLogData]):
    """Creator for one recorded error.

    An error belongs to whoever it happened to, so the row joins that user's scope
    and is reachable through it. The column is nullable because the manager and the
    agents record their own failures through the plugin, where there is no user to
    own the row; those join nothing and stay visible only to the admin read.
    """

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

    @override
    def scope_type(self) -> ScopeType:
        return _ERROR_LOG_SCOPE

    @override
    def scope_id(self, row: ErrorLogRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: ErrorLogRow) -> Collection[ScopeRef]:
        if row.user is None:
            return ()
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=row.user),)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> ErrorLogRow:
        return ErrorLogRow(
            severity=self.severity.value,
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
        )

    @override
    def to_data(self, row: ErrorLogRow) -> ErrorLogData:
        return row.to_dataclass()

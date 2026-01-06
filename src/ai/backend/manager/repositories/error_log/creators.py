from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.models.error_log import ErrorLogRow
from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.data.error_log.types import ErrorLogData

__all__ = ("ErrorLogCreatorSpec",)


class ErrorLogCreatorSpec(CreatorSpec[ErrorLogRow]):
    def __init__(self, data: ErrorLogData) -> None:
        self._data = data

    @override
    def build_row(self) -> ErrorLogRow:
        return ErrorLogRow(
            severity=self._data.severity,
            source=self._data.source,
            message=self._data.message,
            context_lang=self._data.context_lang,
            context_env=self._data.context_env,
            user=self._data.user,
            is_read=self._data.is_read,
            is_cleared=self._data.is_cleared,
            request_url=self._data.request_url,
            request_status=self._data.request_status,
            traceback=self._data.traceback,
        )

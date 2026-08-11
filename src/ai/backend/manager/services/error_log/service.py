from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.errors.resource import DBOperationFailed

from .actions.mark_cleared import MarkClearedErrorLogAction, MarkClearedErrorLogActionResult
from .actions.search import SearchErrorLogsAction, SearchErrorLogsActionResult

if TYPE_CHECKING:
    from ai.backend.manager.repositories.error_log import ErrorLogRepository

__all__ = ("ErrorLogService",)


@dataclass
class ErrorLogService:
    """Service for error log operations."""

    _repository: ErrorLogRepository

    def __init__(self, repository: ErrorLogRepository) -> None:
        self._repository = repository

    async def list_logs(self, action: SearchErrorLogsAction) -> SearchErrorLogsActionResult:
        """List error logs with role-based visibility."""
        items, total_count = await self._repository.list_logs(
            user_uuid=action.user_uuid,
            user_domain=action.user_domain,
            is_superadmin=action.is_superadmin,
            is_admin=action.is_admin,
            page_no=action.page_no,
            page_size=action.page_size,
            mark_read=action.mark_read,
        )
        return SearchErrorLogsActionResult(logs=items, total_count=total_count)

    async def mark_cleared(
        self, action: MarkClearedErrorLogAction
    ) -> MarkClearedErrorLogActionResult:
        """Mark an error log as cleared."""
        rowcount = await self._repository.mark_cleared(
            log_id=action.log_id,
            user_uuid=action.user_uuid,
            user_domain=action.user_domain,
            is_superadmin=action.is_superadmin,
            is_admin=action.is_admin,
        )
        if rowcount != 1:
            raise DBOperationFailed(f"Failed to update error log: {action.log_id}")
        return MarkClearedErrorLogActionResult()

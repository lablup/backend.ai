from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.errors.resource import DBOperationFailed

from .actions import CreateErrorLogAction, CreateErrorLogActionResult
from .actions.list import ListErrorLogsAction, ListErrorLogsActionResult
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

    async def create(self, action: CreateErrorLogAction) -> CreateErrorLogActionResult:
        """Creates a new error log."""
        error_log_data = await self._repository.create(action.creator)
        return CreateErrorLogActionResult(error_log_data=error_log_data)

    async def search(self, action: SearchErrorLogsAction) -> SearchErrorLogsActionResult:
        """Search error logs with querier pattern."""
        result = await self._repository.search(action.querier)
        return SearchErrorLogsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def list_logs(self, action: ListErrorLogsAction) -> ListErrorLogsActionResult:
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
        return ListErrorLogsActionResult(logs=items, total_count=total_count)

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

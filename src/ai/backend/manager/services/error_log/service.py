from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .actions import CreateErrorLogAction, CreateErrorLogActionResult
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

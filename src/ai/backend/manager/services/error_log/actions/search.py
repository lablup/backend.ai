from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.error_log.types import ErrorLogData

from .base import ErrorLogGlobalAction


@dataclass
class SearchErrorLogsAction(ErrorLogGlobalAction):
    """Action to list error logs with role-based visibility."""

    user_uuid: uuid.UUID
    user_domain: str
    is_superadmin: bool
    is_admin: bool
    page_no: int
    page_size: int
    mark_read: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_error_logs"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchErrorLogsActionResult(BaseActionResult):
    """Result of listing error logs."""

    logs: list[ErrorLogData]
    total_count: int

    @override
    def entity_id(self) -> str | None:
        return None

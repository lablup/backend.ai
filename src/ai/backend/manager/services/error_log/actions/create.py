from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.repositories.base import Creator

from .base import ErrorLogAction

if TYPE_CHECKING:
    from ai.backend.manager.models.error_logs import ErrorLogRow


@dataclass
class CreateErrorLogAction(ErrorLogAction):
    """Action to create an error log."""

    creator: Creator[ErrorLogRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class CreateErrorLogActionResult(BaseActionResult):
    """Result of creating an error log."""

    error_log_data: ErrorLogData

    @override
    def entity_id(self) -> str | None:
        return str(self.error_log_data.id)

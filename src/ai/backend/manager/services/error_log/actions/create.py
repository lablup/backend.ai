from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
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
    def operation_type(cls) -> str:
        return "create"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class CreateErrorLogActionResult(BaseActionResult):
    """Result of creating an error log."""

    error_log_data: ErrorLogData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.error_log_data.id)

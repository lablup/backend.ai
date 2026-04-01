from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ErrorLogAction


@dataclass
class MarkClearedErrorLogAction(ErrorLogAction):
    """Action to mark an error log as cleared."""

    log_id: uuid.UUID
    user_uuid: uuid.UUID
    user_domain: str
    is_superadmin: bool
    is_admin: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.log_id)


@dataclass
class MarkClearedErrorLogActionResult(BaseActionResult):
    """Result of marking an error log as cleared."""

    @override
    def entity_id(self) -> str | None:
        return None

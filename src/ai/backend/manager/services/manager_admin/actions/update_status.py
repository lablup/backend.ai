from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ManagerAdminAction


@dataclass
class UpdateManagerStatusAction(ManagerAdminAction):
    """Action to update the manager status."""

    status: str
    force_kill: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UpdateManagerStatusActionResult(BaseActionResult):
    """Result of updating manager status."""

    @override
    def entity_id(self) -> str | None:
        return None

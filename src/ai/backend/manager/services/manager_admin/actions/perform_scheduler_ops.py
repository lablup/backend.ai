from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ManagerAdminAction


@dataclass
class PerformSchedulerOpsAction(ManagerAdminAction):
    """Action to perform a scheduler operation (include/exclude agents)."""

    agent_ids: list[str]
    schedulable: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class PerformSchedulerOpsActionResult(BaseActionResult):
    """Result of performing a scheduler operation."""

    @override
    def entity_id(self) -> str | None:
        return None

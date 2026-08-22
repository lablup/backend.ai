from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class PerformSchedulerOpsAction(BaseGlobalAction):
    """Action to perform a scheduler operation (include/exclude agents)."""

    agent_ids: list[str]
    schedulable: bool

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MANAGER_ADMIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "perform_scheduler_ops"


@dataclass
class PerformSchedulerOpsActionResult:
    """Result of performing a scheduler operation."""

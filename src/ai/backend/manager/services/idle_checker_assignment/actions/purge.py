from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentRelationAction,
)


@dataclass(frozen=True)
class PurgeIdleCheckerAssignmentAction(IdleCheckerAssignmentRelationAction):
    """Unlink a scope from an idle checker for good."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_idle_checker_assignment"

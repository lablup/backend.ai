from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentRelationAction,
)


@dataclass(frozen=True)
class DisableIdleCheckerAssignmentAction(IdleCheckerAssignmentRelationAction):
    """Switch a binding off. The row stays and both sides keep reading each other."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disable_idle_checker_assignment"


@dataclass(frozen=True)
class EnableIdleCheckerAssignmentAction(IdleCheckerAssignmentRelationAction):
    """Switch a binding back on."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.RESTORE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "enable_idle_checker_assignment"

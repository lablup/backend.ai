from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.idle_checker.creators import IdleCheckerAssignmentCreator
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentRelationAction,
)


@dataclass(frozen=True)
class CreateIdleCheckerAssignmentAction(IdleCheckerAssignmentRelationAction):
    """Bind an idle checker definition to one scope."""

    creator: IdleCheckerAssignmentCreator

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_idle_checker_assignment"

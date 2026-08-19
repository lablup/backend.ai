from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerAssignmentCreatorSpec
from ai.backend.manager.services.idle_checker_assignment.actions.base import (
    IdleCheckerAssignmentAction,
)


@dataclass
class CreateIdleCheckerAssignmentAction(IdleCheckerAssignmentAction):
    creator_spec: IdleCheckerAssignmentCreatorSpec

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateIdleCheckerAssignmentActionResult(BaseActionResult):
    data: IdleCheckerAssignmentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)

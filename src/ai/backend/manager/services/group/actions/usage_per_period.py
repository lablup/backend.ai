from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.group.actions.base import GroupAction


# TODO: Change to batch action
@dataclass
class UsagePerPeriodAction(GroupAction):
    start_date: str
    end_date: str
    project_id: UUID | None = None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class UsagePerPeriodActionResult(BaseActionResult):
    # TODO: Define return type
    result: list[Any]

    @override
    def entity_id(self) -> str | None:
        return None

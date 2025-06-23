from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.actions.base import GroupAction


# TODO: Change to batch action
@dataclass
class UsagePerPeriodAction(GroupAction):
    start_date: str
    end_date: str
    project_id: Optional[UUID] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "usage_per_period"


@dataclass
class UsagePerPeriodActionResult(BaseActionResult):
    # TODO: Define return type
    result: list[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None

from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.group.base import GroupAction


# TODO: Batch action 변경
@dataclass
class UsagePerMonthAction(GroupAction):
    month: str
    group_ids: Optional[list[UUID]] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "usage_per_month"


@dataclass
class UsagePerMonthActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    result: list[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None

from dataclasses import dataclass
from typing import Any, Optional, Self, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class UsagePerMonthAction(ResourceAction):
    group_ids: list[str]
    month: str

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return ""

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

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return ""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Self):
            return False
        return True

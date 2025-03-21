from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class UsagePerPeriodAction(ResourceAction):
    start_date: str
    end_date: str
    project_id: Optional[UUID] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "usage_per_period"


@dataclass
class UsagePerPeriodActionResult(BaseActionResult):
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
        if not isinstance(other, type(self)):
            return False
        return True

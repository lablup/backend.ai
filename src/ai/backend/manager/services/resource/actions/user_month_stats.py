from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class UserMonthStatsAction(ResourceAction):
    user_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "user_month_stats"


@dataclass
class UserMonthStatsActionResult(BaseActionResult):
    stats: list[Any]

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

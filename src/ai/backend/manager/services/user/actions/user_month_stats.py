from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.user.actions.base import UserAction


@dataclass
class UserMonthStatsAction(UserAction):
    user_id: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_id

    @override
    def operation_type(self):
        return "user_month_stats"


@dataclass
class UserMonthStatsActionResult(BaseActionResult):
    stats: list[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None

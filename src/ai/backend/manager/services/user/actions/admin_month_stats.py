from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.user.actions.base import UserAction


# TODO: Batch action으로 만든 후 entity_id엔 모든 user_id를 넣어야 함.
@dataclass
class AdminMonthStatsAction(UserAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "admin_month_stats"


@dataclass
class AdminMonthStatsActionResult(BaseActionResult):
    stats: list[Any]

    @override
    def entity_id(self) -> Optional[str]:
        return None

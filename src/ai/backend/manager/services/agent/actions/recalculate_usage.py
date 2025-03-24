from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.base import AgentAction


# TODO: 이게 AgentService가 맞나? SessionService가 맞나?
# TODO: BatchAction으로 만들기.
@dataclass
class RecalculateUsageAction(AgentAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "recalculate_usage"


@dataclass
class RecalculateUsageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

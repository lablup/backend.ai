from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RecalculateUsageAction(AgentAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "recalculate_usage"


# TODO: Change this to BatchAction and return the list of all agent ids.
@dataclass
class RecalculateUsageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

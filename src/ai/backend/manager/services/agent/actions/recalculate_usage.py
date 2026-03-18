from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RecalculateUsageAction(AgentAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


# TODO: Change this to BatchAction and return the list of all agent ids.
@dataclass
class RecalculateUsageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

from dataclasses import dataclass
from typing import override

from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class GetTotalResourcesAction(AgentAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetTotalResourcesActionResult(BaseActionResult):
    total_resources: TotalResourceData

    @override
    def entity_id(self) -> str | None:
        return None

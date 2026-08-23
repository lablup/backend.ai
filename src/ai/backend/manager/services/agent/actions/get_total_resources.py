from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class GetTotalResourcesAction(BaseGlobalAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_agent_total_resources"


@dataclass(frozen=True)
class GetTotalResourcesActionResult:
    total_resources: TotalResourceData

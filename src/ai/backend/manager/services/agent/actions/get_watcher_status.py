from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class GetWatcherStatusAction(BaseGlobalAction):
    agent_id: AgentId

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
        return "global_get_agent_watcher_status"


@dataclass(frozen=True)
class GetWatcherStatusActionResult:
    data: dict[str, Any]
    agent_id: AgentId

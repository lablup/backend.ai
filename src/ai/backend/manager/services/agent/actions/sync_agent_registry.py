from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.agent.types import AgentData


@dataclass(frozen=True)
class SyncAgentRegistryAction(BaseGlobalAction):
    agent_id: AgentId

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_sync_agent_registry"


@dataclass(frozen=True)
class SyncAgentRegistryActionResult:
    # TODO: Add proper type
    result: Any
    agent_data: AgentData

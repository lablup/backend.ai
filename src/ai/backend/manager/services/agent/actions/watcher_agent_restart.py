from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.agent.actions.base import (
    AgentSingleEntityAction,
    AgentSingleEntityActionResult,
)


@dataclass
class WatcherAgentRestartAction(AgentSingleEntityAction):
    agent_id: AgentId

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.agent_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.AGENT, str(self.agent_id))


@dataclass
class WatcherAgentRestartActionResult(AgentSingleEntityActionResult):
    data: dict[str, Any]
    agent_id: AgentId

    @override
    def target_entity_id(self) -> str:
        return str(self.agent_id)

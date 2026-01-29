from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class SyncAgentRegistryAction(AgentAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "sync_agent_registry"


@dataclass
class SyncAgentRegistryActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    agent_data: AgentData

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_data.id)

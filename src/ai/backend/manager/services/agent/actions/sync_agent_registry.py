from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class SyncAgentRegistryAction(AgentAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "sync_agent_registry"


@dataclass
class SyncAgentRegistryActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    agent_row: AgentRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_row.id)

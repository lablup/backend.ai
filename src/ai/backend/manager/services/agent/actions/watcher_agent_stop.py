from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class WatcherAgentStopAction(AgentAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

    @override
    def operation_type(self):
        return "watcher_agent_stop"


@dataclass
class WatcherAgentStopActionResult(BaseActionResult):
    # TODO: Add proper type
    resp: Any
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

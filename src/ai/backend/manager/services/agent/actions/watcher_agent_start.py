from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.base import AgentAction


@dataclass
class WatcherAgentStartAction(AgentAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

    @override
    def operation_type(self):
        return "watcher_agent_start"


@dataclass
class WatcherAgentStartActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    resp: Any

    @override
    def entity_id(self) -> Optional[str]:
        return None

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class WatcherAgentStartAction(AgentAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "watcher_agent_start"


@dataclass
class WatcherAgentStartActionResult(BaseActionResult):
    data: dict[str, Any]
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

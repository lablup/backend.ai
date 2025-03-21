from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource.base import ResourceAction


@dataclass
class WatcherAgentStartAction(ResourceAction):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return None

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

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return ""

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return True

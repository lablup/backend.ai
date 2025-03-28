from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class AgentAction(BaseAction):
    @override
    def entity_type(self):
        return "agent"


@dataclass
class AgentBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "agent"

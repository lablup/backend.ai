from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class SessionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "session"


@dataclass
class SessionBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "session"

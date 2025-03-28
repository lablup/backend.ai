from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class UserAction(BaseAction):
    @override
    def entity_type(self):
        return "user"


@dataclass
class UserBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "user"

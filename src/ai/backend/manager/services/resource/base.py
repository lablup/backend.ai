from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ResourceAction(BaseAction):
    @override
    def entity_type(self):
        return "resource"


@dataclass
class ResourceBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "resource"

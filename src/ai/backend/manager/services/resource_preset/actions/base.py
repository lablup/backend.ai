from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ResourcePresetAction(BaseAction):
    @override
    def entity_type(self):
        return "resource_preset"


@dataclass
class ResourcePresetBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "resource_preset"

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ResourcePresetAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "resource_preset"


@dataclass
class ResourcePresetBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "resource_preset"

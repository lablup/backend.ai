from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ImageAction(BaseAction):
    @override
    def entity_type(self):
        return "image"


@dataclass
class ImageBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "image"

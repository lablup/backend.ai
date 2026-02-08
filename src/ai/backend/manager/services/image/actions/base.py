from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ImageAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE


@dataclass
class ImageBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE

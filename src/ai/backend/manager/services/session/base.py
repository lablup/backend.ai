from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class SessionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION


@dataclass
class SessionBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

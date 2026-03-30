from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


class ObjectStorageAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.OBJECT_STORAGE

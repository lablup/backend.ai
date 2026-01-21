from typing import override

from ai.backend.manager.actions.action import BaseAction


class ObjectStorageAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "object_storage"

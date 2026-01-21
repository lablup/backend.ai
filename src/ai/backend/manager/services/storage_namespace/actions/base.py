from typing import override

from ai.backend.manager.actions.action import BaseAction


class StorageNamespaceAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "storage_namespace"

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.storage_namespace.actions.base import StorageNamespaceAction


@dataclass
class UnregisterNamespaceAction(StorageNamespaceAction):
    storage_id: uuid.UUID
    namespace: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "unregister"


@dataclass
class UnregisterNamespaceActionResult(BaseActionResult):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage_namespace.creator import StorageNamespaceCreator
from ai.backend.manager.data.object_storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.base import StorageNamespaceAction


@dataclass
class RegisterNamespaceAction(StorageNamespaceAction):
    creator: StorageNamespaceCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "register"


@dataclass
class RegisterNamespaceActionResult(BaseActionResult):
    storage_id: uuid.UUID
    result: StorageNamespaceData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.storage_id)

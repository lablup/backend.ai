import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.services.storage_namespace.actions.base import StorageNamespaceAction


@dataclass
class GetNamespacesAction(StorageNamespaceAction):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetNamespacesActionResult(BaseActionResult):
    result: list[StorageNamespaceData]

    @override
    def entity_id(self) -> str | None:
        return None

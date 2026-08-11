import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.storage_namespace.actions.base import (
    StorageNamespaceGlobalAction,
)


@dataclass
class UnregisterNamespaceAction(StorageNamespaceGlobalAction):
    """Remove one namespace from a storage.

    Service-kept: the row is addressed by ``(storage_id, namespace)``, and the purge
    specs key on a single primary value. ``PURGE`` because the row leaves the table —
    the storage namespace carries no lifecycle column.
    """

    storage_id: uuid.UUID
    namespace: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "unregister_storage_namespace"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class UnregisterNamespaceActionResult(BaseActionResult):
    storage_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.storage_id)

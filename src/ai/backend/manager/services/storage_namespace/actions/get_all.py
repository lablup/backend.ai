import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.storage_namespace.actions.base import (
    StorageNamespaceGlobalAction,
)


@dataclass
class GetAllNamespacesAction(StorageNamespaceGlobalAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_namespaces_by_storage"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAllNamespacesActionResult(BaseActionResult):
    result: dict[uuid.UUID, list[str]]

    @override
    def entity_id(self) -> str | None:
        return None

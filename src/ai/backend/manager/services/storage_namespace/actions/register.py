from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.creators import StorageNamespaceCreator
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass
class RegisterNamespaceAction(CreateGlobalOpsAction[StorageNamespaceRow, StorageNamespaceData]):
    """Register a namespace under an object storage."""

    creator: StorageNamespaceCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "register_storage_namespace"

    @override
    def to_creator(self) -> StorageNamespaceCreator:
        return self.creator

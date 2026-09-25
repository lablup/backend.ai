from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass(frozen=True)
class GetNamespacesAction(ScopedSearchOpsAction[StorageNamespaceRow, StorageNamespaceData]):
    """Read the namespaces the named object storages hold.

    Search-shaped rather than a get: what comes back is a list, and the storage
    selects it rather than identifying a row.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return StorageNamespaceEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_namespaces_of_storage"

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.storage_namespace.conditions import StorageNamespaceConditions
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.repositories.storage_namespace.searchers import StorageNamespaceSearcher


@dataclass
class GetNamespacesAction(SearchGlobalOpsAction[StorageNamespaceRow, StorageNamespaceData]):
    """Read the namespaces one object storage holds.

    Search-shaped rather than a get: what comes back is a list, and the storage id
    selects it rather than identifying a row.
    """

    storage_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_namespaces_of_storage"

    @override
    def to_searcher(self) -> StorageNamespaceSearcher:
        return StorageNamespaceSearcher(
            pagination=NoPagination(),
            conditions=[StorageNamespaceConditions.by_storage_id(self.storage_id)],
        )

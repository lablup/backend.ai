from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.repositories.storage_namespace.searchers import StorageNamespaceSearcher


@dataclass
class SearchStorageNamespacesAction(
    SearchGlobalOpsAction[StorageNamespaceRow, StorageNamespaceData]
):
    """Page through registered namespaces."""

    searcher: StorageNamespaceSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_namespaces"

    @override
    def to_searcher(self) -> StorageNamespaceSearcher:
        return self.searcher

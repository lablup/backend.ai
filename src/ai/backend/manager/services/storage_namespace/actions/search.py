from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass(frozen=True)
class SearchStorageNamespacesAction(
    GlobalSearcherOpsAction[StorageNamespaceRow, StorageNamespaceData]
):
    """Page through registered namespaces."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return StorageNamespaceEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_namespaces"

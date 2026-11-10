from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace.queriers import (
    BulkStorageNamespaceQuerier,
)
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass
class BulkGetStorageNamespacesAction(
    PartialBulkGetEntityOpsAction[StorageNamespaceRow, StorageNamespaceData]
):
    """Read the storage namespaces the caller named, answering for each id."""

    ids: Sequence[StorageNamespaceID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_storage_namespaces"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkStorageNamespaceQuerier:
        return BulkStorageNamespaceQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])

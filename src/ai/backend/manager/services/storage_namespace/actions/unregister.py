from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import (
    StorageNamespaceID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.models.storage_namespace.purgers import StorageNamespacePurger


@dataclass
class UnregisterNamespaceAction(PurgeEntityOpsAction[StorageNamespaceRow, StorageNamespaceData]):
    """Remove one namespace from a storage.

    Addressed by id; callers holding only the (storage, namespace) pair resolve it
    through the lookup first. PURGE because the row leaves the table.
    """

    id: StorageNamespaceID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "unregister_storage_namespace"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> StorageNamespacePurger:
        return StorageNamespacePurger(storage_namespace_id=self.id)

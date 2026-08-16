from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.storage_namespace import StorageNamespaceID
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass
class StorageNamespacePurger(EntityPurger[StorageNamespaceRow, StorageNamespaceData]):
    """Purger for removing one namespace from a storage."""

    storage_namespace_id: StorageNamespaceID

    @override
    def row_class(self) -> type[StorageNamespaceRow]:
        return StorageNamespaceRow

    @override
    def pk_value(self) -> StorageNamespaceID:
        return self.storage_namespace_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.storage_namespace_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return row.to_dataclass()

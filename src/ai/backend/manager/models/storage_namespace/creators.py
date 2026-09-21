from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import (
    StorageNamespaceID,
)
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.storage_namespace.searchable_fields import (
    StorageNamespaceSearchableFields,
)


@dataclass
class StorageNamespaceCreator(
    CreatedInGlobal[StorageNamespaceRow], EntityCreator[StorageNamespaceRow, StorageNamespaceData]
):
    """Creator for one namespace registered under an object storage."""

    storage_id: uuid.UUID
    namespace: str

    @override
    def entity_id(self, row: StorageNamespaceRow) -> StorageNamespaceID:
        return StorageNamespaceID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> StorageNamespaceRow:
        return StorageNamespaceRow(storage_id=self.storage_id, namespace=self.namespace)

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return StorageNamespaceSearchableFields.own.to_data(row)

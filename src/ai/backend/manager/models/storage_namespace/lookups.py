"""DataLookup implementations for the storage namespace repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow


@dataclass
class StorageNamespaceLookup(DataLookup[StorageNamespaceRow, StorageNamespaceID]):
    """Resolves the storage a namespace sits in, plus the namespace, into that row.

    The pair is the table's unique constraint, so it names one row; the id is a
    surrogate that callers of the registration API never held.
    """

    storage_id: uuid.UUID
    namespace: str

    @override
    def row_class(self) -> type[StorageNamespaceRow]:
        return StorageNamespaceRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: StorageNamespaceRow.storage_id == self.storage_id,
            lambda: StorageNamespaceRow.namespace == self.namespace,
        ]

    @override
    def to_entity_id(self, row: StorageNamespaceRow) -> StorageNamespaceID:
        return row.id

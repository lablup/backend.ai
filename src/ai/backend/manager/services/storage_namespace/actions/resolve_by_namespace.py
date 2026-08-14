from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.repositories.storage_namespace.lookups import (
    StorageNamespaceByStorageAndName,
)


@dataclass(frozen=True)
class StorageNamespaceKey(LookupKey):
    """The pair a caller names a namespace by, standing in for the row's id."""

    storage_id: uuid.UUID
    namespace: str

    @override
    def kind(self) -> str:
        return "storage_namespace_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"storage_id": str(self.storage_id), "namespace": self.namespace}


@dataclass
class ResolveStorageNamespaceAction(
    LookupEntityOpsAction[StorageNamespaceRow, StorageNamespaceData]
):
    """Resolve a (storage, namespace) pair into the row it names.

    Registration exposes the pair rather than the id, so removal has to translate
    one into the other before it can address a row. Keeping that as its own read
    leaves the purge keyed on the primary value like every other purge.
    """

    storage_id: uuid.UUID
    namespace: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "resolve_storage_namespace"

    @override
    def lookup_key(self) -> StorageNamespaceKey:
        return StorageNamespaceKey(storage_id=self.storage_id, namespace=self.namespace)

    @override
    def to_lookup(self) -> StorageNamespaceByStorageAndName:
        return StorageNamespaceByStorageAndName(
            storage_id=self.storage_id, namespace=self.namespace
        )

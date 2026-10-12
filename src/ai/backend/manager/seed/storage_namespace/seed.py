from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.manager.models.storage_namespace.upserters import StorageNamespaceUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class StorageNamespaceSeed(SeedItem):
    """One ``storage_namespace`` row, keyed by its id, in the storage ``storage_id`` names."""

    id: StorageNamespaceID
    storage_id: ObjectStorageID
    namespace: str = Field(min_length=1)

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=StorageNamespaceUpserter(
                id=self.id, storage_id=self.storage_id, namespace=self.namespace
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[StorageNamespaceSeed]]) -> list[SeedRejection]:
        return []

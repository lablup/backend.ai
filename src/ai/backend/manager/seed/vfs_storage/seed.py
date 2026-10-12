from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.models.vfs_storage.upserters import VFSStorageUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class VFSStorageSeed(SeedItem):
    """One ``vfs_storages`` row, keyed by its id."""

    id: VFSStorageID
    name: str = Field(min_length=1)
    host: str = Field(min_length=1)
    base_path: str = Field(min_length=1)

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=VFSStorageUpserter(
                id=self.id, name=self.name, host=self.host, base_path=self.base_path
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[VFSStorageSeed]]) -> list[SeedRejection]:
        return []

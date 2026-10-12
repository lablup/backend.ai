from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.manager.models.object_storage.upserters import ObjectStorageUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ObjectStorageSeed(SeedItem):
    """One ``object_storages`` row, keyed by its id."""

    id: ObjectStorageID
    name: str = Field(min_length=1)
    host: str = Field(min_length=1)
    access_key: str
    secret_key: str
    endpoint: str = Field(min_length=1)
    region: str | None = None

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ObjectStorageUpserter(
                id=self.id,
                name=self.name,
                host=self.host,
                access_key=self.access_key,
                secret_key=self.secret_key,
                endpoint=self.endpoint,
                region=self.region,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ObjectStorageSeed]]) -> list[SeedRejection]:
        return []

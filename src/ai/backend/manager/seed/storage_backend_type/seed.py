from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendCapability,
    StorageBackendType,
)
from ai.backend.manager.models.storage_backend.upserters import StorageBackendTypeUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class StorageBackendTypeSeed(SeedItem):
    """One ``storage_backend_types`` row, keyed by its name."""

    name: str = Field(min_length=1, max_length=64)
    capabilities: frozenset[StorageBackendCapability]

    @override
    def key(self) -> str:
        return self.name

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=StorageBackendTypeUpserter(
                name=StorageBackendType(self.name),
                capabilities=StorageBackendCapabilities(supported=self.capabilities),
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[StorageBackendTypeSeed]]) -> list[SeedRejection]:
        return []

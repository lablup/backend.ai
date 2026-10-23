from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.manager.models.global_entity.upserters import GlobalEntityUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class GlobalEntitySeed(SeedItem):
    """One ``global_entities`` row and its node, keyed by its name."""

    id: GlobalEntityID
    name: GlobalEntityName

    @override
    def key(self) -> str:
        return self.name.value

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=GlobalEntityUpserter(id=self.id, name=self.name),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[GlobalEntitySeed]]) -> list[SeedRejection]:
        return []

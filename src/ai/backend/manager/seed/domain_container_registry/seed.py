from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.manager.models.domain_container_registry_relation.creators import (
    DomainContainerRegistryRelationCreator,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRelationWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class DomainContainerRegistrySeed(SeedRelationItem):
    """One registry allowed for a domain, linked as the domain API allows one."""

    domain_id: DomainID
    registry_id: ContainerRegistryID

    @override
    def key(self) -> str:
        return f"{self.domain_id}:{self.registry_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=DomainContainerRegistryRelationCreator(),
            scope=self.domain_id,
            target=self.registry_id,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[DomainContainerRegistrySeed]]) -> list[SeedRejection]:
        """None: a pair already linked is skipped when it is written."""
        return []

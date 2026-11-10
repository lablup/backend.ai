from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.models.container_registry.creators import ContainerRegistryProjectCreator
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRelationWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class ContainerRegistryProjectSeed(SeedRelationItem):
    """One registry allowed on a project, linked as the registry API links one, and
    the project's default registry when ``is_default`` is set."""

    registry_id: ContainerRegistryID
    project_id: ProjectID
    is_default: bool = False

    @override
    def key(self) -> str:
        return f"{self.registry_id}:{self.project_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=ContainerRegistryProjectCreator(is_default=self.is_default),
            scope=self.project_id,
            target=self.registry_id,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(
        cls, files: Sequence[SeedItems[ContainerRegistryProjectSeed]]
    ) -> list[SeedRejection]:
        """None: a second default registry for a project fails its own item when it is
        written."""
        return []
